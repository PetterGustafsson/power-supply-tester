"""Local, serial-backed calibration wizard for the Rev D/D2 tester.

Uses protocol 2 to retain all twelve low points in device NVS. Only explicit
operator captures send cal0/calv; calstatus/calbegin synchronize the pass. The serial connection stays open independently of browser navigation.
"""
from __future__ import annotations
import argparse
import collections
import csv
import datetime as dt
import json
import math
from pathlib import Path
import queue
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NOMINAL_GAIN = 1 + 2_000_000 / 4700
STATE_NAMES = ['No voltage', 'Supply', 'Check wiring', 'Above 18 V', 'ADC fault', 'Calibration incomplete']

def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def clean(value):
    if isinstance(value, float) and not math.isfinite(value): return None
    if isinstance(value, dict): return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,collections.deque)): return [clean(v) for v in value]
    return value

def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n')
    tmp.replace(path)

class UserError(Exception): pass

class Controller:
    def __init__(self, data_dir, prior_gains=None, prior_mask=0, restart=False, clock=time.monotonic):
        self.data_dir=Path(data_dir);self.data_dir.mkdir(parents=True,exist_ok=True)
        self.clock=clock;self.lock=threading.RLock();self.outbox=queue.Queue()
        self.connected=False;self.connection_id=0;self.sample=None;self.sample_at=None
        self.history=collections.deque(maxlen=240);self.valid_streak=0
        self.pending=None;self.device_ready=False;self.maintenance=False;self.copied_mask=0;self.supports_copy=False
        self.notice='First capture all twelve inputs at 0 V, then all twelve at 12 V. Start with the DC output off.'
        self.error=None;self.last_ack=None;self.last_ack_at=None
        self.gains={int(k):float(v) for k,v in (prior_gains or {}).items()};self.device_mask=prior_mask
        stored=self.data_dir/'stored.json'
        if stored.exists():
            record=json.loads(stored.read_text())
            self.gains.update({int(k):float(v) for k,v in record.get('gains',{}).items()})
            self.device_mask=int(record.get('device_mask',prior_mask));self.copied_mask=int(record.get('copied_mask',0))
        state=self.data_dir/'pass.json'
        p=json.loads(state.read_text()) if state.exists() and not restart else {}
        if p.get('workflow')=='two-pass-v2':
            self.pass_id=p['pass_id'];self.batch_id=p['batch_id'];self.current=int(p['current'])
            self.phase=p['phase'];self.zeros=p['zeros'];self.completed=p['completed'];self.started=p['started_at']
            self.shared_source=p.get('shared_source');self.checks=p.get('checks',[])
            self.notice='Checking the calibration saved on the tester…'
        else:self._new_pass()
        self._persist()

    @property
    def pass_dir(self): return self.data_dir/'passes'/self.pass_id

    def _new_pass(self):
        self.batch_id=uuid.uuid4().hex[:8].upper()
        self.pass_id=dt.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+self.batch_id.lower()
        self.started=timestamp();self.current=1;self.phase='low';self.zeros={};self.completed={}
        self.device_ready=False;self.error=None;self.shared_source=None;self.checks=[]

    def _persist(self):
        p=dict(workflow='two-pass-v2',pass_id=self.pass_id,batch_id=self.batch_id,current=self.current,
               phase=self.phase,zeros=self.zeros,completed=self.completed,shared_source=self.shared_source,checks=self.checks,started_at=self.started,updated_at=timestamp())
        write_json(self.data_dir/'pass.json',p);write_json(self.pass_dir/'pass.json',p)

    def event(self,kind,**data):
        self.pass_dir.mkdir(parents=True,exist_ok=True)
        with (self.pass_dir/'events.jsonl').open('a') as f:
            f.write(json.dumps(clean({'at':timestamp(),'kind':kind,**data}),allow_nan=False)+'\n')

    def _clear_jobs(self):
        while not self.outbox.empty():
            try:self.outbox.get_nowait()
            except queue.Empty:break

    def _queue(self,kind,command,**data):
        self.pending=dict(kind=kind,command=command,started=self.clock(),connection_id=self.connection_id,**data)
        self.outbox.put(dict(command=command,connection_id=self.connection_id))

    def _query_status(self):
        self.device_ready=False;self._clear_jobs();self._queue('status','calstatus')

    def connection(self,connected,reason=None):
        with self.lock:
            interrupted=self.pending and self.pending['kind'] in ('low','high')
            self.connected=connected;self.connection_id+=1;self.device_ready=False
            self.sample=None;self.sample_at=None;self.history.clear();self.valid_streak=0
            self.pending=None;self._clear_jobs()
            if interrupted:self.error='Capture interrupted. Recheck the displayed point and capture it again after USB recovers.'
            if connected:self._query_status()
            self.event('connected' if connected else 'disconnected',reason=reason)

    def on_line(self,line):
        with self.lock:
            with (self.data_dir/'serial.log').open('a') as f:f.write(line+'\n')
            row=next(csv.reader([line]),[])
            if len(row)==23:
                try:
                    raw=list(map(float,row[2:14]));refs=list(map(float,row[14:18]))
                    valid=int(row[1])==1 and all(math.isfinite(v) for v in raw+refs)
                    self.sample=dict(sequence=int(row[0]),valid=valid,raw=raw,refs=refs,
                                     state=int(row[18]),supply_V=float(row[22]),positive_mask=int(row[19],16),return_mask=int(row[20],16))
                except (ValueError,IndexError):return
                self.sample_at=self.clock()
                signals=[raw[i]-refs[i%4] for i in range(12)] if valid else [None]*12
                self.history.append(dict(at=self.sample_at,signals=signals,valid=valid,supply_V=self.sample['supply_V'],state=self.sample['state']))
                self.valid_streak=self.valid_streak+1 if valid else 0
                return
            if line.startswith(('ESP-ROM:','TESTER12V Rev D:')):
                self.sample=None;self.sample_at=None;self.history.clear();self.valid_streak=0
                self.device_ready=False;self.pending=None;self._clear_jobs()
                if line.startswith('TESTER12V Rev D:') and self.connected:self._query_status()
                self.event('boot',line=line);return
            if not line.startswith(('CAL_','COMMANDS:')):return
            self.last_ack=line;self.last_ack_at=timestamp();self.event('ack',line=line)
            status=re.fullmatch(r'CAL_STATUS protocol=2 batch=([0-9A-Fa-f]{8}) low_mask=([0-9A-Fa-f]+) done_mask=([0-9A-Fa-f]+) mask=([0-9A-Fa-f]+) zero=([01])(?: copied_mask=([0-9A-Fa-f]+))?',line)
            pending=self.pending
            if status:
                if not pending or pending['kind'] not in ('status','begin'):return
                self.pending=None;self._clear_jobs();self.device_mask=int(status[4],16)
                self.supports_copy=status[6] is not None;self.copied_mask=int(status[6] or '0',16)
                if status[5]!='1':
                    self.error='The saved open-input baseline is missing. Stop calibration and check the tester settings.';return
                if status[1].upper()!=self.batch_id:
                    if self.zeros or self.completed:
                        self.error='The tester holds a different calibration pass. Start again from input 1 to create a matching pass.';return
                    self._queue('begin','calbegin '+self.batch_id);return
                expected=sum(1<<(int(k)-1) for k in self.zeros)
                expected_done=sum(1<<(int(k)-1) for k in self.completed)
                if int(status[3],16)&expected_done!=expected_done or self.device_mask&expected_done!=expected_done:
                    self.error='Some completed gains are missing on the tester. Start again from input 1.';return
                if int(status[2],16)&expected!=expected:
                    self.error='Some saved 0 V points are missing on the tester. Start again from input 1.';return
                if self.phase=='test' and (self.device_mask!=0xfff or self.copied_mask!=0xffe):
                    self.error='Shared calibration changed on the tester. Reapply INP1 before testing.';return
                self.device_ready=True
                self.notice=('Shared gain loaded. Remove AGND before testing a numbered pin pair.' if self.phase=='test' else 'Tester connected. Saved 0 V points are retained across USB reconnects. Follow the current checklist.')
                return
            if not pending:return
            if line.startswith(('CAL_ERROR','COMMANDS:')):
                self.pending=None;self._clear_jobs()
                self.error=('This firmware does not support the two-pass workflow.' if line.startswith('COMMANDS:') and pending['kind'] in ('begin','status')
                    else 'The tester rejected the capture: '+line+'. Recheck the displayed step and retry.')
                return
            copied=re.fullmatch(r'CAL_COPIED source=1 gain=([\d.]+) mask=FFF copied_mask=FFE',line)
            if copied and pending['kind']=='shared':
                gain=float(copied[1])
                if not 380<=gain<=480:
                    self.pending=None;self.error='Unexpected shared gain acknowledgement.';return
                self.gains={pin:gain for pin in range(1,13)};self.device_mask=0xfff;self.copied_mask=0xffe
                self.shared_source=dict(pin=1,gain=gain,acknowledgement=line,saved_at=self.last_ack_at,
                    provenance='Existing measured INP1 calibration; gain copied to INP2–INP12. Separate open-input baselines retained.')
                self.phase='test';self.current=1;self.pending=None;self.error=None
                self.notice='INP1 gain is applied to all inputs. Remove the AGND connection before testing pin pairs.'
                write_json(self.data_dir/'stored.json',dict(gains=self.gains,device_mask=self.device_mask,copied_mask=self.copied_mask,shared_source=self.shared_source,updated_at=timestamp()))
                self.event('shared_gain_saved',**self.shared_source);self._persist();return
            low=re.fullmatch(r'CAL_LOW_SAVED pin=(\d+) batch=([0-9A-Fa-f]{8}) low_mask=([0-9A-Fa-f]+)',line)
            saved=re.fullmatch(r'CAL_SAVED pin=(\d+) gain=([\d.]+) mask=([0-9A-Fa-f]+) batch=([0-9A-Fa-f]{8})',line)
            if low and pending['kind']=='low' and int(low[1])==pending['pin'] and low[2].upper()==self.batch_id:
                if not int(low[3],16)&(1<<(self.current-1)):return
                record=dict(pin=self.current,meter_V=pending['meter'],meter_input=pending['meter_input'],
                    captured_at=self.last_ack_at,acknowledgement=line,preview_low_signal_V=pending['low_signal'],
                    preview_uses_reference_ratio_approximation=True,low_point_storage='Device NVS, tied to batch '+self.batch_id)
                self.zeros[str(self.current)]=record
                write_json(self.pass_dir/f'input-{self.current}-low.json',record)
                self.phase='low_saved';self.pending=None;self.error=None
                self.notice=f'0 V point for input {self.current} saved. Turn the output OFF before moving the red lead.'
                self._persist();return
            if saved and pending['kind']=='high' and int(saved[1])==pending['pin'] and saved[4].upper()==self.batch_id:
                gain=float(saved[2]);mask=int(saved[3],16)
                if not (380<=gain<=480 and mask&(1<<(self.current-1))):
                    self.pending=None;self.error='Unexpected gain acknowledgement. Recheck this point and retry.';return
                record=dict(pin=self.current,gain=gain,reference_voltage_V=pending['meter'],
                            meter_input=pending['meter_input'],saved_at=self.last_ack_at,
                            acknowledgement=line,device_mask=mask,source='Operator multimeter entry',
                            command=pending['command'],saved_to_device_NVS=True)
                self.completed[str(self.current)]=record;self.gains[self.current]=gain;self.device_mask=mask
                write_json(self.pass_dir/f'input-{self.current}-calibration.json',record)
                self.copied_mask&=~(1<<(self.current-1))
                write_json(self.data_dir/'stored.json',dict(gains=self.gains,device_mask=mask,copied_mask=self.copied_mask,updated_at=timestamp()))
                self.phase='saved';self.pending=None;self.error=None
                self.notice=f'Input {self.current} saved using {pending["meter_input"]} V from the multimeter.'
                self._persist()

    def fresh(self):
        return bool(self.connected and self.sample and self.sample['valid'] and
                    self.sample_at is not None and self.clock()-self.sample_at<2.5)

    def _check_ready(self,payload):
        if self.pending:raise UserError('A capture or USB check is running. Keep the voltage steady.')
        if not self.device_ready:raise UserError('Wait for the tester to verify this calibration pass.')
        if payload.get('pass_id')!=self.pass_id or payload.get('pin')!=self.current:
            raise UserError('The current input changed. Follow the refreshed instructions.')
        if payload.get('confirmed') is not True:raise UserError('Confirm that the connections match the checklist.')
        if not self.fresh() or self.valid_streak<4:
            raise UserError('Wait for a stable, live ADC connection before capturing.')
        recent=[h['signals'][self.current-1] for h in list(self.history)[-4:]]
        if len(recent)<4 or any(v is None for v in recent) or max(recent)-min(recent)>.0003:
            raise UserError('The reading is changing. Hold the voltage and connections steady.')
        try:meter=float(payload.get('meter',''))
        except (ValueError,TypeError):raise UserError('Enter the actual multimeter reading.')
        if not math.isfinite(meter):raise UserError('Enter a finite multimeter reading.')
        signals=self.history[-1]['signals']
        others=[i+1 for i,s in enumerate(signals) if i+1!=self.current and abs(s)>.00045]
        if others:raise UserError('Leave the other inputs open. A connection is visible on input '+', '.join(map(str,others))+'.')
        return meter,sum(recent)/len(recent),signals[self.current-1]

    def action(self,kind,payload):
        with self.lock:
            if kind=='shared':
                if self.pending or not self.device_ready:raise UserError('Wait for the USB check or capture to finish.')
                if payload.get('pass_id')!=self.pass_id:raise UserError('Reload this page before changing the calibration mode.')
                if not self.supports_copy:raise UserError('The shared-gain firmware update must be loaded first.')
                if not self.device_mask&1 or self.copied_mask&1:raise UserError('INP1 must have a measured calibration before it can be copied.')
                self._queue('shared','calcopy 1');self.notice='Applying the saved INP1 gain to all twelve channels…';self.error=None
                self.event('shared_gain_requested',source=1);return
            if kind=='check':
                if self.phase!='test' or not self.device_ready or not self.fresh() or self.valid_streak<4:
                    raise UserError('Wait for live shared-gain readings before recording a check.')
                if payload.get('pass_id')!=self.pass_id or payload.get('confirmed') is not True:
                    raise UserError('Confirm the displayed test wiring and current pass.')
                try:
                    plus=int(payload['plus']);minus=int(payload['minus']);meter=float(payload['meter'])
                except (ValueError,TypeError,KeyError):raise UserError('Select two inputs and enter the actual multimeter voltage.')
                if not 1<=plus<=12 or not 1<=minus<=12 or plus==minus:raise UserError('Use two different numbered inputs.')
                if not math.isfinite(meter) or not 9<=meter<=18:raise UserError('Use a multimeter reading from 9 to 18 V for this functional check.')
                recent=list(self.history)[-4:]
                if self.sample['state']!=1 or len(recent)<4 or any(h['state']!=1 or not h['valid'] for h in recent):
                    raise UserError('Wait for a stable live supply reading. Check both numbered connections and remove AGND.')
                volts=[h['supply_V'] for h in recent]
                if max(volts)-min(volts)>.05:raise UserError('Hold the voltage and connections steady before recording.')
                measured=sum(volts)/len(volts);error=measured-meter
                wiring=self.sample['positive_mask']==1<<(plus-1) and self.sample['return_mask']==1<<(minus-1)
                record=dict(at=timestamp(),plus=plus,minus=minus,meter_V=meter,measured_V=measured,error_V=error,
                    tolerance_V=.10,wiring_matches=wiring,passed=abs(error)<=.10 and wiring,
                    positive_mask=self.sample['positive_mask'],return_mask=self.sample['return_mask'],copied_gain_mask=self.copied_mask)
                self.checks.append(record);self.event('supply_check',**record);self.error=None;self._persist();return
            if kind=='restart':
                if self.pending:raise UserError('Wait for the capture or USB check to finish before starting again.')
                if payload.get('pass_id')!=self.pass_id:raise UserError('This page is out of date. Reload before restarting.')
                self.event('pass_ended',completed=list(self.completed),zeros=list(self.zeros))
                self._new_pass();self._clear_jobs()
                self.notice='New two-pass calibration: all 0 V points first, then all 12 V points. Existing gains are retained until replaced.'
                if self.connected:self._query_status()
                self.event('new_pass');self._persist();return
            if kind=='next':
                if self.pending or self.phase not in ('low_saved','saved'):raise UserError('Capture this point before continuing.')
                if payload.get('pass_id')!=self.pass_id or payload.get('pin')!=self.current:
                    raise UserError('The current input changed. Refresh this step.')
                self.error=None
                if self.phase=='low_saved':
                    if self.current==12:self.current=1;self.phase='high';self.notice='All 0 V points saved. Start the 12 V pass at input 1.'
                    else:self.current+=1;self.phase='low';self.notice='Keep the supply set to 0.00 V. Turn its output OFF before moving the red lead.'
                elif self.current==12:self.phase='complete';self.notice='All twelve inputs were saved in this pass.'
                else:self.current+=1;self.phase='high';self.notice='Keep the supply set to 12 V. Turn its output OFF before moving the red lead.'
                self._persist();return
            if kind not in ('low','high'):raise UserError('Unknown action.')
            if self.phase!=kind:raise UserError('Follow the current step before capturing another point.')
            meter,average_signal,signal=self._check_ready(payload)
            if kind=='low':
                if abs(meter)>.02:raise UserError('Set the supply to 0.00 V. The meter should be within 0.02 V of zero.')
                if not -.003<signal<-.00045:
                    raise UserError(f'INP{self.current} does not look connected to 0 V relative to AGND. Check the highlighted terminal and AGND lead.')
                command=f'cal0 {self.current}'
            else:
                if len(self.zeros)!=12 or str(self.current) not in self.zeros:
                    raise UserError('Complete all twelve 0 V points before the 12 V pass.')
                if not 10<meter<14:raise UserError('Use a multimeter reading above 10 V and below 14 V, normally about 12 V.')
                delta=signal-self.zeros[str(self.current)]['preview_low_signal_V']
                if delta<=0 or not 380<meter/delta<480:
                    raise UserError('The live signal does not match the entered voltage. Check the input, polarity and meter reading.')
                command=f'calv {self.current} {meter:.6f}'
            self._queue(kind,command,pin=self.current,meter=meter,meter_input=str(payload['meter']).strip(),low_signal=average_signal)
            self.error=None;self.notice='Capturing the 0 V point…' if kind=='low' else 'Saving this input…'
            self.event('command_requested',command=command,meter=meter,confirmed=True)

    def timeout_check(self):
        with self.lock:
            if self.pending and self.clock()-self.pending['started']>15:
                kind=self.pending['kind'];self.pending=None;self._clear_jobs()
                if kind in ('status','begin'):
                    self.error='The tester is not answering. Check USB; reconnecting will retry the connection check.'
                else:self.error='No capture acknowledgement received. Recheck the displayed point and capture it again.'

    def fail_transport(self,reason):self.connection(False,reason)

    def snapshot(self):
        with self.lock:
            self.timeout_check();now=self.clock();fresh=self.fresh();p=self.current-1
            sample=self.sample if fresh else None
            raw=sample['raw'][p] if sample else None;ref=sample['refs'][p%4] if sample else None
            zero=self.zeros.get(str(self.current));preview=None
            if sample and zero is not None:
                preview=(raw-ref-zero['preview_low_signal_V'])*self.gains.get(self.current,NOMINAL_GAIN)
            graph=[dict(seconds=round(h['at']-now,2),signal_mV=None if h['signals'][p] is None else h['signals'][p]*1000)
                   for h in self.history if now-h['at']<=60]
            actual=sample['supply_V'] if sample and sample['state'] in (0,1,3) else None
            return clean(dict(maintenance=self.maintenance,workflow='two-pass-v2',pass_id=self.pass_id,batch_id=self.batch_id,current=self.current,phase=self.phase,
                zeros=self.zeros,zero_count=len(self.zeros),completed=self.completed,completed_count=len(self.completed),copied_mask=self.copied_mask,supports_copy=self.supports_copy,shared_source=self.shared_source,checks=self.checks[-30:],stored_count=self.device_mask.bit_count(),
                device_mask=self.device_mask,connected=self.connected,device_ready=self.device_ready,fresh=fresh,
                ready=fresh and self.valid_streak>=4 and self.device_ready,busy=bool(self.pending),valid_streak=self.valid_streak,
                age_s=None if self.sample_at is None else round(now-self.sample_at,2),
                adc_fault=bool(self.connected and self.sample and self.sample['state']==4),
                unstable=bool(self.connected and self.sample and not self.sample['valid'] and self.sample['state']==2),
                raw_V=raw,reference_V=ref,signal_mV=None if raw is None else (raw-ref)*1000,
                preview_V=preview,actual_pair_V=actual,
                device_state=STATE_NAMES[self.sample['state']] if self.sample and 0<=self.sample['state']<6 else 'Waiting for data',
                sequence=self.sample['sequence'] if self.sample else None,
                channels=[dict(pin=i+1,raw_V=sample['raw'][i] if sample else None,
                    signal_mV=(sample['raw'][i]-sample['refs'][i%4])*1000 if sample else None,
                    saved=bool(self.device_mask&(1<<i)),copied=bool(self.copied_mask&(1<<i)),polarity=('+' if sample and sample['state'] in (1,3) and sample['positive_mask']&(1<<i) else '−' if sample and sample['state'] in (1,3) and sample['return_mask']&(1<<i) else '?'),zero_this_pass=str(i+1) in self.zeros,this_pass=str(i+1) in self.completed) for i in range(12)],
                graph=graph,error=self.error,notice=self.notice,last_ack=self.last_ack,last_ack_at=self.last_ack_at,updated_at=timestamp()))

class SerialBridge(threading.Thread):
    def __init__(self,controller,port):
        super().__init__(daemon=True);self.controller=controller;self.port=port;self.stop_event=threading.Event()
    def run(self):
        import serial
        while not self.stop_event.is_set():
            s=None
            try:
                s=serial.Serial(port=None,baudrate=115200,timeout=.1,exclusive=True)
                s.port=self.port;s.dtr=False;s.rts=False;s.open()
                self.controller.connection(True);print('USB_CONNECTED '+self.port,flush=True)
                buffer=bytearray()
                while not self.stop_event.is_set():
                    self.controller.timeout_check()
                    try:job=self.controller.outbox.get_nowait()
                    except queue.Empty:job=None
                    if job:
                        with self.controller.lock:
                            pending=self.controller.pending
                            if pending and job['connection_id']==self.controller.connection_id and job['command']==pending['command']:
                                s.write((job['command']+'\n').encode());s.flush()
                                self.controller.event('command_sent',command=job['command'])
                    buffer.extend(s.read(max(1,s.in_waiting)))
                    while b'\n' in buffer:
                        line,_,rest=buffer.partition(b'\n');buffer=bytearray(rest)
                        self.controller.on_line(line.decode('utf-8',errors='replace').rstrip('\r'))
                    if len(buffer)>16384:buffer.clear()
            except (OSError,serial.SerialException) as exc:
                self.controller.fail_transport(str(exc));print('USB_DISCONNECTED '+str(exc),flush=True)
                self.stop_event.wait(2)
            finally:
                if s is not None:s.close()

def make_handler(controller,token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def valid_host(self):
            return self.headers.get('Host','').split(':')[0] in ('127.0.0.1','localhost')
        def send_bytes(self,status,data,kind):
            self.send_response(status);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','SAMEORIGIN')
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
        def send_json(self,status,data):self.send_bytes(status,json.dumps(clean(data),allow_nan=False).encode(),'application/json')
        def do_GET(self):
            if not self.valid_host():self.send_json(403,{'error':'Local host only.'});return
            path=urlparse(self.path).path
            if path=='/api/state':
                result=controller.snapshot();result['api_token']=token;self.send_json(200,result);return
            if path=='/api/export':self.send_json(200,dict(state=controller.snapshot(),gains=controller.gains));return
            files={'/':(HERE/'static/index.html','text/html; charset=utf-8'),
                   '/app.js':(HERE/'static/app.js','text/javascript; charset=utf-8'),
                   '/style.css':(HERE/'static/style.css','text/css; charset=utf-8'),
                   '/board.png':(REPO/'hardware/rev-d/previews/pcb-top-labels.png','image/png')}
            if path not in files:self.send_json(404,{'error':'Not found.'});return
            file,kind=files[path];self.send_bytes(200,file.read_bytes(),kind)
        def do_POST(self):
            if not self.valid_host():self.send_json(403,{'error':'Local host only.'});return
            origin=self.headers.get('Origin')
            if origin and urlparse(origin).netloc!=self.headers.get('Host'):
                self.send_json(403,{'error':'Local origin required.'});return
            if self.headers.get('X-Calibration-Token')!=token:
                self.send_json(403,{'error':'Reload the page before capturing.'});return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                self.send_json(415,{'error':'JSON required.'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=4096:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict):raise ValueError()
            except (ValueError,json.JSONDecodeError):self.send_json(400,{'error':'Invalid request.'});return
            action=urlparse(self.path).path.removeprefix('/api/')
            try:controller.action(action,payload)
            except UserError as exc:self.send_json(409,{'error':str(exc)});return
            self.send_json(202,controller.snapshot())
    return Handler

def prior_calibration():
    gains={};mask=0
    for p in (REPO/'output/bringup-2026-10-17').glob('input-*-calibration.json'):
        try:
            r=json.loads(p.read_text());pin=int(r['pin']);gains[pin]=float(r['gain']);mask|=1<<(pin-1)
        except (ValueError,KeyError):continue
    return gains,mask

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial-port',default='/dev/cu.usbmodem58760426031')
    parser.add_argument('--http-port',type=int,default=8765)
    parser.add_argument('--data-dir',type=Path,default=REPO/'output/calibration-ui')
    parser.add_argument('--restart-pass',action='store_true')
    parser.add_argument('--maintenance',action='store_true',help='Serve the page without opening USB while firmware is updated.')
    args=parser.parse_args();gains,mask=prior_calibration()
    controller=Controller(args.data_dir,gains,mask,restart=args.restart_pass)
    token=secrets.token_urlsafe(32)
    server=ThreadingHTTPServer(('127.0.0.1',args.http_port),make_handler(controller,token))
    bridge=None
    if args.maintenance:
        controller.maintenance=True;controller.notice='Firmware update waiting for BOOT/RESET. DC output OFF; USB readings paused.'
    else:
        bridge=SerialBridge(controller,args.serial_port);bridge.start()
    write_json(args.data_dir/'server.json',dict(pid=__import__('os').getpid(),port=args.http_port,
               serial_port=args.serial_port,url=f'http://127.0.0.1:{args.http_port}',started_at=timestamp()))
    print(f'LOCAL_URL http://127.0.0.1:{args.http_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        if bridge:bridge.stop_event.set();bridge.join(2)
        server.server_close()

if __name__=='__main__':main()
