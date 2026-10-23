"""Capture guards and two-pass protocol tests; never open the real serial port."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from server import Controller,UserError,make_handler

class Clock:
    def __init__(self):self.value=100.
    def __call__(self):return self.value

def csv_line(pin=1,signal=-.0013,valid=True,seq=1,extra_pin=None):
    refs=[.5762]*4;raw=[.5762]*12;raw[pin-1]+=signal
    if extra_pin:raw[extra_pin-1]-=.0013
    return ','.join(map(str,[seq,int(valid),*raw,*refs,5,'000','000','FFF',0]))

def handshake(c,lowmask=0,done=0):
    c.connection(True)
    assert c.outbox.get_nowait()['command']=='calstatus'
    c.on_line(f'CAL_STATUS protocol=2 batch={c.batch_id} low_mask={lowmask:03X} done_mask={done:03X} mask=003 zero=1')
    assert c.device_ready

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.clock=Clock()
        self.c=Controller(Path(self.tmp.name),{1:427.719635,2:427.1662292},3,clock=self.clock)
        handshake(self.c)
    def tearDown(self):self.tmp.cleanup()
    def feed(self,pin=None,signal=-.0013,valid=True,extra_pin=None):
        for i in range(6):
            self.clock.value+=.5;self.c.on_line(csv_line(pin or self.c.current,signal,valid,i,extra_pin))
    def payload(self,meter='0.00',confirmed=True):
        return dict(pin=self.c.current,pass_id=self.c.pass_id,meter=meter,confirmed=confirmed)
    def low(self):
        pin=self.c.current;self.feed();self.c.action('low',self.payload())
        self.assertEqual(self.c.outbox.get_nowait()['command'],f'cal0 {pin}')
        self.c.on_line(f'CAL_LOW_SAVED pin={pin} batch={self.c.batch_id} low_mask={(1<<pin)-1:03X}')
    def all_zeros(self):
        for pin in range(1,13):
            self.assertEqual(self.c.current,pin);self.assertEqual(self.c.phase,'low')
            self.low();self.assertEqual(self.c.phase,'low_saved');self.c.action('next',self.payload())
        self.assertEqual(self.c.current,1);self.assertEqual(self.c.phase,'high')
    def test_start_preserves_existing_gains(self):
        self.assertEqual(self.c.current,1);self.assertEqual(self.c.completed,{})
        self.assertEqual(self.c.device_mask,3);self.assertTrue(self.c.outbox.empty())
    def test_low_requires_meter_confirmation_and_selected_connection(self):
        self.feed(pin=3)
        with self.assertRaises(UserError):self.c.action('low',self.payload())
        self.feed()
        for data in (self.payload(confirmed=False),self.payload('0.2'),self.payload('nan')):
            with self.assertRaises(UserError):self.c.action('low',data)
        self.assertTrue(self.c.outbox.empty())
    def test_other_inputs_must_be_open(self):
        self.feed(extra_pin=3)
        with self.assertRaisesRegex(UserError,'other inputs open'):self.c.action('low',self.payload())
    def test_stale_faulted_and_changing_readings_block_capture(self):
        self.feed();self.clock.value+=3
        with self.assertRaises(UserError):self.c.action('low',self.payload())
        self.feed(valid=False)
        with self.assertRaises(UserError):self.c.action('low',self.payload())
        self.feed();self.c.on_line(csv_line(signal=-.0025))
        with self.assertRaisesRegex(UserError,'changing'):self.c.action('low',self.payload())
    def test_only_matching_pin_and_batch_ack_advances(self):
        self.feed();self.c.action('low',self.payload());self.c.outbox.get_nowait()
        for ack in (f'CAL_LOW_SAVED pin=2 batch={self.c.batch_id} low_mask=002',
                    'CAL_LOW_SAVED pin=1 batch=00000000 low_mask=001'):
            self.c.on_line(ack);self.assertEqual(self.c.phase,'low')
        self.c.on_line(f'CAL_LOW_SAVED pin=1 batch={self.c.batch_id} low_mask=001')
        self.assertEqual(self.c.phase,'low_saved');self.assertEqual(len(self.c.zeros),1)
        self.c.action('next',self.payload());self.assertEqual(self.c.current,2);self.assertEqual(self.c.phase,'low')
    def test_high_cannot_start_before_all_zeros(self):
        self.low();self.feed(signal=.02675)
        with self.assertRaises(UserError):self.c.action('high',self.payload('11.98'))
        self.assertEqual(self.c.completed,{})
    def test_all_zeros_before_any_high_and_exact_meter_reference(self):
        self.all_zeros();self.assertEqual(self.c.completed,{})
        self.feed(signal=.02675);self.c.action('high',self.payload('11.98'))
        self.assertEqual(self.c.outbox.get_nowait()['command'],'calv 1 11.980000')
        self.assertEqual(self.c.completed,{})
        self.c.on_line(f'CAL_SAVED pin=1 gain=427.1 mask=003 batch={self.c.batch_id}')
        self.assertEqual(self.c.phase,'saved');self.assertEqual(self.c.completed['1']['reference_voltage_V'],11.98)
        self.c.action('next',self.payload());self.assertEqual(self.c.current,2);self.assertEqual(self.c.phase,'high')
    def test_reconnect_retains_zeros_but_requires_device_verification(self):
        self.all_zeros();self.c.connection(False,'unplugged');self.c.connection(True)
        self.feed(signal=.02675)
        with self.assertRaises(UserError):self.c.action('high',self.payload('12'))
        self.assertEqual(self.c.outbox.get_nowait()['command'],'calstatus')
        self.c.on_line(f'CAL_STATUS protocol=2 batch={self.c.batch_id} low_mask=FFF done_mask=000 mask=003 zero=1')
        self.c.action('high',self.payload('12'));self.assertTrue(self.c.snapshot()['busy'])
    def test_boot_does_not_silently_discard_saved_zeros(self):
        self.low();self.c.on_line('ESP-ROM:esp32s3-20210327')
        self.assertEqual(len(self.c.zeros),1);self.assertFalse(self.c.device_ready)
        self.c.on_line('TESTER12V Rev D: real ADC input');self.assertEqual(self.c.outbox.get_nowait()['command'],'calstatus')
    def test_wrong_device_pass_or_missing_device_zeros_blocks_capture(self):
        self.all_zeros();self.c.connection(True);self.c.outbox.get_nowait()
        self.c.on_line('CAL_STATUS protocol=2 batch=00000000 low_mask=FFF done_mask=000 mask=003 zero=1')
        self.assertFalse(self.c.device_ready);self.assertTrue(self.c.outbox.empty())
        self.c.connection(True);self.c.outbox.get_nowait()
        self.c.on_line(f'CAL_STATUS protocol=2 batch={self.c.batch_id} low_mask=7FF done_mask=000 mask=003 zero=1')
        self.assertFalse(self.c.device_ready);self.assertIn('missing',self.c.error)
    def test_new_pass_clears_only_device_batch_metadata(self):
        self.low();old=self.c.pass_id;gain=self.c.gains.copy()
        self.c.action('restart',self.payload());self.assertNotEqual(old,self.c.pass_id)
        self.assertEqual(self.c.zeros,{});self.assertEqual(self.c.gains,gain);self.assertEqual(self.c.device_mask,3)
        self.assertEqual(self.c.outbox.get_nowait()['command'],'calstatus')
        self.c.on_line('CAL_STATUS protocol=2 batch=00000000 low_mask=000 done_mask=000 mask=003 zero=1')
        self.assertEqual(self.c.outbox.get_nowait()['command'],'calbegin '+self.c.batch_id)
        self.c.on_line(f'CAL_STATUS protocol=2 batch={self.c.batch_id} low_mask=000 done_mask=000 mask=003 zero=1')
        self.assertTrue(self.c.device_ready)
    def test_old_firmware_and_missing_baseline_are_blocked(self):
        self.c.connection(True);self.c.outbox.get_nowait();self.c.on_line('COMMANDS: zero; cal0; calv; defaults')
        self.assertFalse(self.c.device_ready);self.assertIn('firmware',self.c.error)
        self.c.connection(True);self.c.outbox.get_nowait()
        self.c.on_line(f'CAL_STATUS protocol=2 batch={self.c.batch_id} low_mask=000 done_mask=000 mask=003 zero=0')
        self.assertFalse(self.c.device_ready);self.assertIn('baseline',self.c.error)
    def test_server_reload_restores_points_then_verifies_device(self):
        self.all_zeros();reopened=Controller(Path(self.tmp.name),clock=self.clock)
        self.assertEqual(reopened.phase,'high');self.assertEqual(len(reopened.zeros),12)
        self.assertFalse(reopened.device_ready);handshake(reopened,0xfff)
    def test_high_ranges_and_wrong_signal_rejected(self):
        self.all_zeros();self.feed(signal=.02675)
        for value in ('10','14','12junk','nan'):
            with self.assertRaises(UserError):self.c.action('high',self.payload(value))
        self.feed(signal=.006)
        with self.assertRaises(UserError):self.c.action('high',self.payload('12'))
        self.assertTrue(self.c.outbox.empty())
    def test_error_timeout_and_reconnect_never_resend_capture(self):
        self.all_zeros();self.feed(signal=.02675);self.c.action('high',self.payload('12'))
        self.c.outbox.get_nowait();self.c.on_line('CAL_ERROR acquisition')
        self.assertEqual(self.c.phase,'high');self.assertEqual(len(self.c.zeros),12)
        self.c.action('high',self.payload('12'));self.clock.value+=16;self.c.timeout_check()
        self.assertFalse(self.c.snapshot()['busy']);self.assertTrue(self.c.outbox.empty())
        self.c.connection(True);self.assertEqual(self.c.outbox.get_nowait()['command'],'calstatus')
        self.assertTrue(self.c.outbox.empty())
    def test_preview_uses_selected_inputs_own_zero(self):
        self.all_zeros();self.c.zeros['1']['preview_low_signal_V']=-.0018
        self.feed(signal=.02675)
        self.assertAlmostEqual(self.c.snapshot()['preview_V'],(.02675+.0018)*self.c.gains[1],places=5)
        self.assertIsNone(self.c.snapshot()['actual_pair_V'])
    def test_changing_connections_are_distinct_from_adc_faults(self):
        row=csv_line(valid=False).split(',');row[18]='2';self.c.on_line(','.join(row))
        snapshot=self.c.snapshot();self.assertFalse(snapshot['adc_fault']);self.assertTrue(snapshot['unstable']);self.assertFalse(snapshot['ready'])
        row[18]='4';self.c.on_line(','.join(row));snapshot=self.c.snapshot()
        self.assertTrue(snapshot['adc_fault']);self.assertFalse(snapshot['unstable'])
    def test_stale_form_cannot_capture_a_different_input_or_pass(self):
        self.feed();p=self.payload();p['pin']=2
        with self.assertRaises(UserError):self.c.action('low',p)
        p=self.payload();p['pass_id']='old'
        with self.assertRaises(UserError):self.c.action('low',p)
    def test_complete_two_passes_and_live_pair_reading(self):
        self.all_zeros()
        for pin in range(1,13):
            self.assertEqual(self.c.current,pin);self.assertEqual(self.c.phase,'high')
            self.feed(signal=.02675);self.c.action('high',self.payload('11.98'));self.c.outbox.get_nowait()
            self.c.on_line(f'CAL_SAVED pin={pin} gain=427.1 mask={3|((1<<pin)-1):03X} batch={self.c.batch_id}')
            self.c.action('next',self.payload())
        self.assertEqual(self.c.phase,'complete');self.assertEqual(self.c.device_mask,0xfff)
        line=csv_line().split(',');line[18]='1';line[22]='12.03';self.c.on_line(','.join(line))
        self.assertEqual(self.c.snapshot()['actual_pair_V'],12.03)

class SharedGainTests(unittest.TestCase):
    setUp=ControllerTests.setUp
    tearDown=ControllerTests.tearDown
    payload=ControllerTests.payload
    def enable_shared(self):
        self.c.supports_copy=True
        self.c.action('shared',self.payload())
        self.assertEqual(self.c.outbox.get_nowait()['command'],'calcopy 1')
        self.assertNotEqual(self.c.phase,'test')
        self.c.on_line('CAL_COPIED source=1 gain=427.9315796 mask=FFF copied_mask=FFE')
        self.assertEqual(self.c.phase,'test')
    def feed_pair(self,voltage=12.04,plus=1,minus=2):
        for i in range(6):
            row=csv_line().split(',');row[18]='1';row[19]=f'{1<<(plus-1):03X}';row[20]=f'{1<<(minus-1):03X}';row[22]=str(voltage)
            self.clock.value+=.5;self.c.on_line(','.join(row))
    def check_payload(self,meter='12.03',plus=1,minus=2):
        return dict(pass_id=self.c.pass_id,meter=meter,plus=plus,minus=minus,confirmed=True)
    def test_copy_requires_supported_firmware_and_measured_source(self):
        with self.assertRaises(UserError):self.c.action('shared',self.payload())
        self.c.supports_copy=True;self.c.copied_mask=1
        with self.assertRaises(UserError):self.c.action('shared',self.payload())
        self.assertTrue(self.c.outbox.empty())
    def test_copy_records_provenance_only_after_device_ack(self):
        self.enable_shared();self.assertEqual(self.c.copied_mask,0xffe)
        self.assertEqual(len(self.c.completed),0)
        self.assertTrue(all(g==427.9315796 for g in self.c.gains.values()))
        saved=json.loads((Path(self.tmp.name)/'stored.json').read_text())
        self.assertEqual(saved['copied_mask'],0xffe)
        self.assertIn('copied',saved['shared_source']['provenance'])
    def test_test_mode_and_copied_flags_survive_reload(self):
        self.enable_shared();reopened=Controller(Path(self.tmp.name),clock=self.clock);reopened.connection(True);reopened.outbox.get_nowait()
        reopened.on_line(f'CAL_STATUS protocol=2 batch={reopened.batch_id} low_mask=000 done_mask=000 mask=FFF zero=1 copied_mask=FFE')
        self.assertTrue(reopened.device_ready);self.assertEqual(reopened.phase,'test');self.assertEqual(reopened.copied_mask,0xffe)
    def test_supply_check_passes_with_matching_voltage_and_direction(self):
        self.enable_shared();self.feed_pair();self.c.action('check',self.check_payload())
        record=self.c.checks[-1];self.assertTrue(record['passed']);self.assertAlmostEqual(record['error_V'],.01)
        self.assertEqual(self.c.copied_mask,0xffe);self.assertEqual(len(self.c.completed),0)
        self.assertEqual(self.c.snapshot()['channels'][0]['polarity'],'+')
        self.assertEqual(self.c.snapshot()['channels'][1]['polarity'],'−')
    def test_voltage_or_polarity_failures_are_recorded_without_adjustment(self):
        self.enable_shared();gain=self.c.gains.copy();self.feed_pair(voltage=12.3)
        self.c.action('check',self.check_payload());self.assertFalse(self.c.checks[-1]['passed'])
        self.feed_pair(plus=2,minus=1);self.c.action('check',self.check_payload())
        self.assertFalse(self.c.checks[-1]['wiring_matches']);self.assertFalse(self.c.checks[-1]['passed']);self.assertEqual(self.c.gains,gain)
    def test_invalid_or_stale_check_not_recorded(self):
        self.enable_shared();self.feed_pair()
        for payload in (self.check_payload(meter='nan'),self.check_payload(plus=1,minus=1),self.check_payload(meter='0')):
            with self.assertRaises(UserError):self.c.action('check',payload)
        self.clock.value+=3
        with self.assertRaises(UserError):self.c.action('check',self.check_payload())
        self.assertEqual(self.c.checks,[])

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.clock=Clock()
        self.c=Controller(Path(self.tmp.name),clock=self.clock);handshake(self.c)
        for i in range(6):self.clock.value+=.5;self.c.on_line(csv_line())
        self.http=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.c,'test-token'))
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.http.server_address[1]}'
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,body=None,headers=None):
        req=Request(self.url+path,data=None if body is None else json.dumps(body).encode(),headers=headers or {})
        return urlopen(req,timeout=3)
    def test_live_json_and_assets_served(self):
        with self.request('/api/state') as r:d=json.load(r)
        self.assertEqual(d['api_token'],'test-token');self.assertTrue(d['fresh']);self.assertEqual(d['zero_count'],0)
        for path in ('/','/app.js','/board.png'):
            with self.request(path) as r:self.assertEqual(r.status,200)
    def test_commands_require_token_and_same_origin(self):
        p=dict(pin=1,pass_id=self.c.pass_id,meter='0.00',confirmed=True)
        for h in ({'Content-Type':'application/json'},
                  {'Content-Type':'application/json','X-Calibration-Token':'test-token','Origin':'https://example.com'}):
            with self.assertRaises(HTTPError) as err:self.request('/api/low',p,h)
            self.assertEqual(err.exception.code,403);err.exception.close()
        self.assertTrue(self.c.outbox.empty())
        h={'Content-Type':'application/json','X-Calibration-Token':'test-token','Origin':self.url}
        with self.request('/api/low',p,h) as r:self.assertEqual(r.status,202)
        self.assertEqual(self.c.outbox.get_nowait()['command'],'cal0 1')

if __name__=='__main__':unittest.main()
