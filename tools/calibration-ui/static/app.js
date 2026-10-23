'use strict';
const $=id=>document.getElementById(id);
let testPlus=1,testMinus=2;
let state=null,token='',phaseKey='',localError='',posting=false,serverAvailable=false;
const centers=[583,626,670,713,830,873,916,960,1077,1120,1163,1207];
const ordinal=n=>['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth'][n-1];
const fmt=(n,d=2)=>Number.isFinite(n)?n.toFixed(d):'—';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function makeStep(s){
  if(s.phase==='test'){makeTest(s);return;}
  const pin=s.current,low=['low','low_saved'].includes(s.phase),complete=s.phase==='complete';
  $('inputLabel').textContent=complete?'ALL INPUTS SAVED':`INPUT ${pin}`;
  $('stageCount').textContent=complete?'COMPLETE':`${low?'0 V':'12 V'} PASS · INPUT ${pin} OF 12`;
  $('stageLow').className='stage '+(low?'active':'done');
  $('stageHigh').className='stage '+(complete?'done':!low?'active':'');
  if(s.phase==='low_saved'||s.phase==='saved'){
    const r=low?s.zeros[String(pin)]:s.completed[String(pin)];
    const nextLabel=low?(pin===12?'Start 12 V pass at input 1 →':`Next 0 V point: input ${pin+1} →`):(pin===12?'Finish calibration →':`Next 12 V point: input ${pin+1} →`);
    $('stepContent').innerHTML=`<div class="saved-icon" aria-hidden="true">✓</div><h2>${low?`Input ${pin}: 0 V saved.`:`Input ${pin} is calibrated.`}</h2><p class="step-subtitle">${low?(pin===12?'All twelve 0 V points are saved. Next, we return to input 1 for the 12 V pass.':'Continue across the inputs at 0 V. The 12 V pass comes after input 12.'):'Both points are saved on the tester for this input.'}</p><div class="reference-saved">Multimeter reference<strong>${esc(r.meter_input)} V</strong></div><ul class="instructions"><li>Turn the DC supply output <strong>OFF</strong> before moving the red lead.</li><li>Keep <strong>black − on AGND</strong> and USB connected.</li><li>${low&&pin<12?'Keep the supply set to <strong>0.00 V</strong>.':!low&&pin<12?'Keep the supply set to about <strong>12 V</strong>.':'Continue below for the next checklist.'}</li></ul><button id="next" class="button capture">${nextLabel}</button>`;
    $('next').addEventListener('click',()=>action('next'));return;
  }
  if(complete){
    $('stepContent').innerHTML='<div class="saved-icon" aria-hidden="true">✓</div><h2>All 12 inputs are calibrated.</h2><p class="step-subtitle">The values are saved on the tester. You can now verify a floating pin pair.</p><ul class="instructions"><li>Turn the DC supply output <strong>OFF</strong>.</li><li><strong>Remove the AGND connection</strong> or lift the pogo pin.</li><li>Connect supply + and − to two different numbered inputs.</li><li>Set about <strong>12 V</strong>, turn the output ON, and compare the live pair voltage with your multimeter.</li></ul>';
    return;
  }
  const bullets=[
    'Turn the DC supply output <strong>OFF</strong>.',
    `Move the <strong>red + lead to INP${pin}</strong> — the ${ordinal(pin)} screw from the left.`,
    'Keep the <strong>black − lead on AGND</strong>, using the pad or pogo pin.',
    'Leave the other <strong>11 numbered inputs open</strong>. Keep USB connected.',
    low?'Set the supply to <strong class="setting">0.00 V</strong>, then turn its output <strong>ON</strong>.':`Set ${pin===1?'the supply to':'or keep the supply at'} approximately <strong class="setting">12 V</strong>, then turn its output <strong>ON</strong>.`,
    low?'Measure between this input and AGND. The multimeter should read approximately <strong>0.00 V</strong>.':'Measure between this input and AGND. Enter the <strong>actual multimeter reading</strong> below, including its displayed decimals.'
  ];
  $('stepContent').innerHTML=`<h2>${low?'0 V pass: capture zero.':'12 V pass: save the reference.'}</h2><p class="step-subtitle">${low?'Work through inputs 1–12 at zero volts first. The supply output must be ON for each capture.':'All twelve 0 V points are saved. Work through inputs 1–12 at about 12 V.'}</p><ul class="instructions">${bullets.map(b=>`<li>${b}</li>`).join('')}</ul><form id="captureForm" class="form-area" novalidate><label class="meter-label" for="meter">${low?'Multimeter reading at zero':'Actual multimeter reading'}</label><div class="meter-box"><input id="meter" type="number" inputmode="decimal" step="any" placeholder="${low?'0.00':'e.g. 11.98'}" autocomplete="off" aria-describedby="meterHint"><span>V</span></div><p id="meterHint" class="meter-hint">${low?'Enter what the meter shows, within ±0.02 V of zero.':'Enter the meter value, even if the supply display differs.'}</p><label class="confirm"><input id="confirmed" type="checkbox"><span>The leads match the highlighted input and AGND. The other 11 inputs are open.</span></label><button id="capture" class="button capture" type="submit" disabled>${low?`Capture INP${pin} at 0 V`:`Save INP${pin} at 12 V`}</button><p id="gate" class="gate-message" aria-live="polite"></p></form>`;
  $('captureForm').addEventListener('submit',event=>{event.preventDefault();if(!$('capture').disabled)action(state.phase,{meter:$('meter').value,confirmed:$('confirmed').checked});});
  for(const id of ['meter','confirmed'])$(id).addEventListener('input',()=>{localError='';updateGate();showError();});
}

function makeTest(s){
  $('inputLabel').textContent='POWER SUPPLY TEST';$('stageCount').textContent='SHARED INP1 GAIN';
  $('stepContent').innerHTML=`<h2>Connect a numbered pin pair.</h2><p class="step-subtitle">INP1's measured gain is saved on all inputs. INP2–INP12 use a copied gain; test them against your meter.</p><ul class="instructions"><li>Turn the DC output <strong>OFF</strong>.</li><li><strong>Remove the AGND wire or lift the pogo pin.</strong></li><li>Connect <strong>red + to <span id="testPlusLabel">INP${testPlus}</span></strong> and <strong>black − to <span id="testMinusLabel">INP${testMinus}</span></strong>.</li><li>Leave the other <strong>10 inputs open</strong>. Keep USB connected.</li><li>Set about <strong class="setting">12 V</strong>, turn the output <strong>ON</strong>, and compare the tester with your multimeter.</li><li>Turn output <strong>OFF before moving leads</strong>. Swap the inputs to check the other direction.</li></ul><div class="test-selectors"><label>Red +<select id="testPlus" aria-label="Positive test input"></select></label><label>Black −<select id="testMinus" aria-label="Negative test input"></select></label><button id="swap" class="button secondary small" type="button">Swap</button></div><form id="testForm" class="form-area" novalidate><label class="meter-label" for="meter">Actual multimeter reading</label><div class="meter-box"><input id="meter" type="number" inputmode="decimal" step="any" placeholder="e.g. 12.03"><span>V</span></div><p class="meter-hint">Optional: record a comparison. Check several input pairs and both polarities.</p><label class="confirm"><input id="confirmed" type="checkbox"><span>These two numbered inputs are connected as shown. AGND is disconnected and the other 10 inputs are open.</span></label><button id="capture" class="button capture" type="submit" disabled>Record supply check</button><p id="gate" class="gate-message" aria-live="polite"></p></form>`;
  const options=Array.from({length:12},(_,i)=>`<option value="${i+1}">INP${i+1}</option>`).join('');
  $('testPlus').innerHTML=options;$('testMinus').innerHTML=options;
  function change(){
    testPlus=Number($('testPlus').value);testMinus=Number($('testMinus').value);
    $('testPlusLabel').textContent='INP'+testPlus;$('testMinusLabel').textContent='INP'+testMinus;
    for(const o of $('testPlus').options)o.disabled=Number(o.value)===testMinus;
    for(const o of $('testMinus').options)o.disabled=Number(o.value)===testPlus;
    $('meter').value='';$('confirmed').checked=false;localError='';render(state);
  }
  $('testPlus').value=testPlus;$('testMinus').value=testMinus;
  for(const o of $('testPlus').options)o.disabled=Number(o.value)===testMinus;
  for(const o of $('testMinus').options)o.disabled=Number(o.value)===testPlus;
  $('testPlus').addEventListener('change',change);$('testMinus').addEventListener('change',change);
  $('swap').addEventListener('click',()=>{const old=$('testPlus').value;$('testPlus').value=$('testMinus').value;$('testMinus').value=old;change();});
  $('testForm').addEventListener('submit',event=>{event.preventDefault();if(!$('capture').disabled)action('check',{meter:$('meter').value,confirmed:$('confirmed').checked,plus:testPlus,minus:testMinus});});
  for(const id of ['meter','confirmed'])$(id).addEventListener('input',()=>{localError='';updateGate();showError();});
}

function gateReason(){
  if(!serverAvailable)return 'Local server unavailable. Retrying automatically…';
  if(!state)return 'Waiting for the tester.';
  if(posting||state.busy)return 'Capturing… keep the voltage and connections steady.';
  if(state.maintenance)return 'Firmware update in progress. Follow the BOOT/RESET step in chat.';
  if(!state.connected)return 'Connect the tester by USB.';
  if(!state.device_ready)return 'Checking the saved calibration pass on the tester…';
  if(state.unstable)return 'Reading changing. Hold the voltage and connections steady.';
  if(state.adc_fault)return 'ADC fault. Check the five-wire harness and board power.';
  if(!state.ready)return 'Waiting for stable live readings…';
  if(state.phase==='test'){
    if(testPlus===testMinus)return 'Choose two different numbered inputs.';
    if(state.device_state!=='Supply')return 'Waiting for a live supply across two numbered inputs. AGND must be disconnected.';
    if(!$('meter')?.value.trim())return 'Enter the multimeter voltage to record a check.';
    const meter=Number($('meter').value);
    if(!Number.isFinite(meter)||meter<9||meter>18)return 'Use a meter reading from 9 to 18 V for this check.';
    if(!$('confirmed')?.checked)return 'Confirm the test connections before recording.';
    return '';
  }
  const others=state.channels.filter(c=>c.pin!==state.current&&c.signal_mV!==null&&Math.abs(c.signal_mV)>.45).map(c=>c.pin);
  if(others.length)return `A connection is visible on INP${others.join(', INP')}. Only INP${state.current} should be connected to the supply.`;
  if(state.phase==='low'&&!(state.signal_mV>-3&&state.signal_mV<-.45))return `Waiting for INP${state.current} at 0 V relative to AGND.`;
  if(state.phase==='high'&&!(state.preview_V>9&&state.preview_V<15))return 'Raise the supply to about 12 V and hold it steady.';
  if(!$('meter')?.value.trim())return 'Enter your multimeter reading above.';
  const meter=Number($('meter').value);
  if(!Number.isFinite(meter))return 'Enter a valid multimeter reading.';
  if(state.phase==='low'&&Math.abs(meter)>.02)return 'The zero-point meter reading must be within ±0.02 V.';
  if(state.phase==='high'&&!(meter>10&&meter<14))return 'The 12 V reference must be above 10 V and below 14 V.';
  if(!$('confirmed')?.checked)return 'Confirm the connections above before capturing.';
  return '';
}
function updateGate(){
  const button=$('capture');if(!button)return;
  const reason=gateReason();button.disabled=!!reason;
  button.textContent=state.phase==='test'?'Record supply check':state.busy?'Capturing…':state.phase==='low'?`Capture INP${state.current} at 0 V`:`Save INP${state.current} at 12 V`;
  $('gate').textContent=reason;
  if($('meter'))$('meter').disabled=state.busy||posting;
  if($('confirmed'))$('confirmed').disabled=state.busy||posting;
}
function showError(){
  const error=localError||state?.error||'';$('error').hidden=!error;$('error').textContent=error;
}
function drawGraph(points){
  const values=points.map(p=>p.signal_mV).filter(Number.isFinite);
  if(!values.length){$('chartLine').setAttribute('d','');$('chartMax').textContent='—';$('chartMin').textContent='—';return;}
  let lo=Math.min(0,...values),hi=Math.max(0,...values),span=Math.max(2,hi-lo);
  const mid=(hi+lo)/2;lo=mid-span*.6;hi=mid+span*.6;
  let path='',pen=false;
  for(const p of points){if(!Number.isFinite(p.signal_mV)){pen=false;continue;}const x=42+(60+Math.max(-60,p.seconds))/60*544,y=95-(p.signal_mV-lo)/(hi-lo)*80;path+=(pen?'L':'M')+x.toFixed(1)+' '+y.toFixed(1)+' ';pen=true;}
  $('chartLine').setAttribute('d',path);$('chartMax').textContent=hi.toFixed(1);$('chartMin').textContent=lo.toFixed(1);
}
function render(s){
  serverAvailable=true;state=s;if(s.api_token)token=s.api_token;
  const testing=s.phase==='test';
  document.body.classList.toggle('testing',testing);$('stages').hidden=testing;
  $('eyebrow').textContent=testing?'ONE MEASURED GAIN · TWELVE INPUTS':'ALL 0 V FIRST · THEN ALL 12 V';
  $('pageTitle').textContent=testing?'Power supply test':'Tester calibration';
  $('pageIntro').textContent=testing?'Live voltage and polarity. Check the copied gains with your supply and multimeter.':'Two passes across inputs 1–12. Follow the checklist and live readings.';
  $('shared').hidden=testing;$('shared').disabled=!s.supports_copy||!s.device_ready||s.busy||posting;
  const key=s.pass_id+':'+s.current+':'+s.phase;
  if(key!==phaseKey){phaseKey=key;localError='';makeStep(s);}
  $('progressText').textContent=testing?'Live pin polarity · + positive, − return, ? open / unknown':`0 V: ${s.zero_count} / 12    ·    12 V: ${s.completed_count} / 12`;
  $('storedText').textContent=testing?'INP1 measured · INP2–12 copied':'Existing saved values stay intact until replaced';
  $('pins').innerHTML=testing?s.channels.map(c=>`<div class="pin ${c.polarity==='+'?'active':c.polarity==='−'?'done':''}" aria-label="INP${c.pin}: ${c.polarity}">${c.pin}<strong>${c.polarity}</strong></div>`).join(''):Array.from({length:12},(_,i)=>{const n=i+1,done=!!(s.zero_count<12?s.zeros:s.completed)[String(n)];return `<div class="pin ${done?'done':n===s.current&&s.phase!=='complete'?'active':''}" aria-label="Input ${n}, ${done?'saved this pass':n===s.current?'current':'pending'}">${done?'<span class="pin-check">✓</span>':''}${n}</div>`;}).join('');
  const health=$('health');
  health.className='pill '+(s.busy||s.unstable?'waiting':s.adc_fault?'fault':s.fresh?'live':'waiting');
  health.textContent=s.maintenance?'Firmware update pending':s.busy?'Capturing…':!s.connected?'USB disconnected':s.unstable?'Reading changing':s.adc_fault?'ADC fault':!s.device_ready?'Checking saved pass…':s.fresh?'Live · ADC healthy':'Waiting for data';
  $('freshness').textContent=s.age_s===null?'Waiting for USB readings':`${s.age_s.toFixed(1)} s since last sample`;
  $('sequence').textContent=s.sequence===null?'USB serial':`Sample ${s.sequence}`;
  $('notice').textContent=s.notice;
  const actual=s.phase==='complete'||testing;
  $('voltageLabel').textContent=actual?'Measured pin-pair voltage':'Voltage preview · approximate';
  $('preview').textContent=fmt(actual?s.actual_pair_V:s.preview_V);
  $('previewHelp').textContent=actual?s.device_state:s.preview_V===null?'Available after capturing the 0 V point.':'Live change since 0 V. Use your meter for calibration.';
  $('adc').textContent=fmt(s.raw_V,4);$('signal').textContent=fmt(s.signal_mV,2)+' mV';
  const cx=centers[(testing?testPlus:s.current)-1];
  for(const id of ['inputHalo','inputCircle'])$(id).setAttribute('cx',cx);
  $('inputLeader').setAttribute('d',`M${cx} 828 V907`);$('inputTag').setAttribute('x',cx-93);
  $('inputTagText').setAttribute('x',cx);$('inputTagText').textContent='+  INP'+(testing?testPlus:s.current);
  $('legendPin').textContent='INP'+(testing?testPlus:s.current);
  $('legendReturn').textContent=testing?'INP'+testMinus:'AGND';
  $('returnTarget').style.display=testing?'':'none';
  if(testing){const x=centers[testMinus-1];for(const id of ['returnHalo','returnCircle'])$(id).setAttribute('cx',x);$('returnLeader').setAttribute('d',`M${x} 760 V729`);$('returnTag').setAttribute('x',x-93);$('returnTagText').setAttribute('x',x);$('returnTagText').textContent='− INP'+testMinus;}
  $('boardDesc').textContent=`Supply positive connects to input ${s.current}, the ${ordinal(s.current)} screw from the left; supply negative stays on the AGND pad at the upper right.`;
  $('groundTarget').style.display=actual?'none':'';$('inputTarget').style.display=actual&&!testing?'none':'';
  if(testing)$('boardDesc').textContent=`Supply positive to INP${testPlus}, negative to INP${testMinus}. AGND must be disconnected.`;
  $('channelRows').innerHTML=s.channels.map(c=>`<tr class="${c.pin===s.current?'selected-row':''}"><td>INP${c.pin}</td><td>${fmt(c.raw_V,6)}</td><td>${fmt(c.signal_mV,3)}</td><td>${c.copied?'Copied INP1 gain':c.saved?'Measured gain':'Pending'}</td><td>${c.zero_this_pass?'0 V ✓':'0 V —'} · ${c.this_pass?'12 V ✓':'12 V —'}</td></tr>`).join('');
  $('restart').textContent=testing?'Calibrate inputs individually':'Start again from input 1';
  $('restart').disabled=s.busy||posting;
  $('testResults').hidden=!testing;
  if(testing)$('checkRows').innerHTML=s.checks.slice().reverse().map(r=>`<tr><td>+${r.plus} / −${r.minus}</td><td>${fmt(r.meter_V)} V</td><td>${fmt(r.measured_V)} V</td><td>${r.error_V>=0?'+':''}${fmt(r.error_V,3)} V</td><td>${r.passed?'Pass':r.wiring_matches?'Check voltage':'Check polarity'}</td></tr>`).join('')||'<tr><td colspan="5">No supply checks recorded yet.</td></tr>';
  if($('next'))$('next').disabled=posting;
  drawGraph(s.graph);updateGate();showError();
}
async function action(name,extra={}){
  if(posting||!state||!serverAvailable)return;
  posting=true;localError='';updateGate();
  try{
    const response=await fetch('/api/'+name,{signal:AbortSignal.timeout(5000),method:'POST',headers:{'Content-Type':'application/json','X-Calibration-Token':token},body:JSON.stringify({pass_id:state.pass_id,pin:state.current,...extra})});
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'The action was not accepted.');
    render(data);
  }catch(error){localError=error.name==='TimeoutError'?'The request timed out. Wait for the live page to confirm the point before moving the lead.':error.message;showError();}
  finally{posting=false;updateGate();if(state)render(state);}
}
async function poll(){
  try{const response=await fetch('/api/state',{cache:'no-store',signal:AbortSignal.timeout(3000)});if(!response.ok)throw new Error();render(await response.json());}
  catch{serverAvailable=false;const health=$('health');health.className='pill fault';health.textContent='Local server unavailable';$('freshness').textContent='Retrying automatically…';updateGate();$('restart').disabled=true;if($('next'))$('next').disabled=true;}
  finally{setTimeout(poll,500);}
}
$('shared').addEventListener('click',()=>action('shared'));
$('restart').addEventListener('click',()=>action('restart'));
poll();
