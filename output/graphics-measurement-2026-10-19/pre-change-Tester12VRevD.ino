#include "DEV_Config.h"
#include "LCD_1in28.h"
#include "Measurement.h"
#include "CalibrationBatch.h"
#include "DisplayGraphics.h"
#include <Preferences.h>

static UWORD frame[240*240];
UWORD *BlackImage=frame;
static Preferences prefs;
static float gain[12], zeroRatio[12], raw[12], reference[4], corrected[12];
static bool calibrated=false, zeroValid=false;
static bool unstableScan=false;
static CalibrationBatch batch;
static uint16_t calibrationMask=0;
static uint16_t copiedGainMask=0;
static uint32_t sequence=0;
static char command[96];
static unsigned commandLength=0;
static tester::Result screenResult;
static bool screenInitialized=false,screenStarting=true,screenCapturing=false,screenUnstable=false;
static uint32_t nextScreenAt=0,lastMeasurementAt=0;
void serviceDisplay();

bool writeReg(uint8_t address,uint8_t reg,uint16_t value) {
  Wire.beginTransmission(address);Wire.write(reg);Wire.write(value>>8);Wire.write(value&255);
  return Wire.endTransmission()==0;
}
bool readReg(uint8_t address,uint8_t reg,uint16_t &value) {
  Wire.beginTransmission(address);Wire.write(reg);
  if (Wire.endTransmission(false)!=0) return false;
  if (Wire.requestFrom(address,(uint8_t)2)!=(uint8_t)2) return false;
  value=((uint16_t)Wire.read()<<8)|Wire.read();return true;
}
bool acquire() {
  float next[12],nextRef[4];
  for(uint8_t channel=0;channel<4;channel++) {
    const uint16_t config=0x8783u|((uint16_t)(4+channel)<<12);
    for(uint8_t bank=0;bank<4;bank++) {
      const uint16_t setting=bank==3?0xc783u:config;
      if(!writeReg(0x48+bank,1,setting))return false;
    }
    const uint32_t began=millis();uint8_t complete=0;
    while(complete!=15) {
      if(millis()-began>50)return false;
      for(uint8_t bank=0;bank<4;bank++) {
        if(complete&(1<<bank))continue;
        uint16_t status,code;const uint16_t setting=bank==3?0xc783u:config;
        if(!readReg(0x48+bank,1,status)||(status&0x7fff)!=(setting&0x7fff))return false;
        if(!(status&0x8000))continue;
        if(!readReg(0x48+bank,0,code))return false;
        const float volts=(int16_t)code*.00003125f;
        if(!std::isfinite(volts)||volts<.20f||volts>.98f)return false;
        if(bank==3){if(volts<.35f||volts>.85f)return false;nextRef[channel]=volts;}else next[bank*4+channel]=volts;
        complete|=1<<bank;
      }
      if(complete!=15)delay(1);
    }
  }
  memcpy(raw,next,sizeof(raw));memcpy(reference,nextRef,sizeof(reference));
  return !zeroValid||tester::normalize(raw,reference,zeroRatio,gain,corrected);
}

// Rendering uses the last complete measurement; acquisition and calibration are unchanged.
void renderScreen() {
  const uint32_t now=millis();
  tester_ui::Options options;
  options.shared=copiedGainMask!=0;options.capturing=screenCapturing;
  options.starting=screenStarting;options.unstable=screenUnstable;
  options.calibrationReady=calibrated;
  options.stale=!screenStarting&&!screenCapturing&&(uint32_t)(now-lastMeasurementAt)>1500;
  tester_ui::render(frame,screenResult,now,options);
  LCD_1IN28_Display(frame);nextScreenAt=millis()+100;
}
void serviceDisplay() {
  if(screenInitialized&&(int32_t)(millis()-nextScreenAt)>=0)renderScreen();
}
void display(const tester::Result &r) {
  screenResult=r;lastMeasurementAt=millis();screenStarting=false;
  screenUnstable=unstableScan;screenInitialized=true;renderScreen();
}
// Calibration takes explicit serial commands and a known voltage source.
// Never automatically zero with an unknown DUT attached.
bool averageRaw(unsigned count=32) {
  struct CaptureScope {
    bool previous;
    explicit CaptureScope(bool capturing):previous(screenCapturing){screenCapturing=capturing;}
    ~CaptureScope(){screenCapturing=previous;}
  } capture(count>=64);
  double sum[12]={0},refSum[4]={0};float low[12],high[12];unstableScan=false;
  for(unsigned n=0;n<count;n++) {
    if(!acquire())return false;
    for(int i=0;i<12;i++) {
      sum[i]+=raw[i];float sample=(raw[i]-zeroRatio[i]*reference[i%4])*gain[i];
      if(n==0)low[i]=high[i]=sample;else{low[i]=fminf(low[i],sample);high[i]=fmaxf(high[i],sample);}
    }
    for(int m=0;m<4;m++)refSum[m]+=reference[m];
    serviceDisplay(); // Only between complete ADC scans; mux/conversion timing stays intact.
  }
  for(int i=0;i<12;i++)if(high[i]-low[i]>.25f)unstableScan=true;
  if(unstableScan)return false; // Do not label an average of changing connections as a stable supply.
  for(int i=0;i<12;i++)raw[i]=sum[i]/count;
  for(int m=0;m<4;m++)reference[m]=refSum[m]/count;
  return !zeroValid||tester::normalize(raw,reference,zeroRatio,gain,corrected);
}
void saveCalibration() {
  prefs.putBytes("ratio",zeroRatio,sizeof(zeroRatio));prefs.putBytes("gain",gain,sizeof(gain));
  prefs.putBool("zeroOK",zeroValid);prefs.putUShort("mask",calibrationMask);
  prefs.putUShort("copied",copiedGainMask);
  calibrated=zeroValid && calibrationMask==0x0fff;
}
bool saveBatch() {
  return prefs.putBytes("batch",&batch,sizeof(batch))==sizeof(batch);
}
void batchStatus() {
  Serial.printf("CAL_STATUS protocol=2 batch=%08lX low_mask=%03X done_mask=%03X mask=%03X zero=%d copied_mask=%03X\n",
    (unsigned long)batch.id,batch.lowMask,batch.doneMask,calibrationMask,zeroValid,copiedGainMask);
}
void serviceCommand() {
  while(Serial.available()) {
    char c=Serial.read();if(c=='\r')continue;
    if(c!='\n'){if(commandLength<sizeof(command)-1)command[commandLength++]=c;else commandLength=0;continue;}
    command[commandLength]=0;commandLength=0;
    int pin;float known;unsigned long batchId;
    if(strcmp(command,"calstatus")==0) {
      batchStatus();
    } else if(sscanf(command,"calcopy %d",&pin)==1 && pin>=1 && pin<=12 && zeroValid &&
              (calibrationMask&(1u<<(pin-1))) && !(copiedGainMask&(1u<<(pin-1)))) {
      const float sourceGain=gain[pin-1];
      if(!std::isfinite(sourceGain)||sourceGain<380||sourceGain>480){Serial.println("CAL_ERROR source gain");continue;}
      for(float &g:gain)g=sourceGain;
      calibrationMask=0x0fff;copiedGainMask=0x0fff&~(1u<<(pin-1));saveCalibration();
      Serial.printf("CAL_COPIED source=%d gain=%.7f mask=%03X copied_mask=%03X\n",pin,sourceGain,calibrationMask,copiedGainMask);
    } else if(sscanf(command,"calbegin %lx",&batchId)==1 && batchId && zeroValid) {
      batch=CalibrationBatch{};batch.id=(uint32_t)batchId;
      if(!saveBatch()){Serial.println("CAL_ERROR storage");continue;}
      batchStatus();
    } else if(strcmp(command,"zero")==0) {
      if(!averageRaw(64)){Serial.println("CAL_ERROR acquisition");continue;}
      float lo=raw[0],hi=raw[0];for(float v:raw){lo=fminf(lo,v);hi=fmaxf(hi,v);}
      if(hi-lo>.004f){Serial.println("CAL_ERROR disconnect ALL test leads before zero");continue;}
      bool ratiosOK=true;for(int i=0;i<12;i++){float r=raw[i]/reference[i%4];if(r<.97f||r>1.03f)ratiosOK=false;}
      if(!ratiosOK){Serial.println("CAL_ERROR reference mismatch");continue;}
      for(int i=0;i<12;i++)zeroRatio[i]=raw[i]/reference[i%4];zeroValid=true;batch=CalibrationBatch{};saveBatch();saveCalibration();
      Serial.println("ZERO_SAVED; this assumes all twelve terminals were open");
    } else if(sscanf(command,"cal0 %d",&pin)==1 && pin>=1 && pin<=12 && zeroValid) {
      if(!averageRaw(64)){Serial.println("CAL_ERROR acquisition");continue;}
      const float low=corrected[pin-1]/gain[pin-1];
      if(!std::isfinite(low)||low>=-.00045f||low<=-.003f){Serial.println("CAL_ERROR check zero voltage and wiring");continue;}
      batch.low[pin-1]=low;batch.lowMask|=1u<<(pin-1);batch.doneMask&=~(1u<<(pin-1));
      if(!saveBatch()){Serial.println("CAL_ERROR storage");continue;}
      Serial.printf("CAL_LOW_SAVED pin=%d batch=%08lX low_mask=%03X\n",pin,(unsigned long)batch.id,batch.lowMask);
    } else if(sscanf(command,"calv %d %f",&pin,&known)==2 && pin>=1 && pin<=12 &&
              (batch.lowMask&(1u<<(pin-1))) && std::isfinite(known) && known>10 && known<14 && zeroValid) {
      if(!averageRaw(64)){Serial.println("CAL_ERROR acquisition");continue;}
      float delta=corrected[pin-1]/gain[pin-1]-batch.low[pin-1];
      float g=known/delta;
      if(!std::isfinite(g)||g<380||g>480){Serial.println("CAL_ERROR check applied voltage and wiring");continue;}
      gain[pin-1]=g;calibrationMask|=1u<<(pin-1);copiedGainMask&=~(1u<<(pin-1));saveCalibration();
      batch.doneMask|=1u<<(pin-1);
      if(!saveBatch()){Serial.println("CAL_ERROR storage");continue;}
      Serial.printf("CAL_SAVED pin=%d gain=%.7f mask=%03X batch=%08lX\n",pin,g,calibrationMask,(unsigned long)batch.id);
    } else if(strcmp(command,"defaults")==0) {
      for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;zeroRatio[i]=1;}
      prefs.clear();calibrationMask=0;copiedGainMask=0;zeroValid=false;calibrated=false;batch=CalibrationBatch{};Serial.println("CAL_CLEARED");
    } else Serial.println("COMMANDS: calstatus; calcopy <measured source pin>; calbegin <hex pass id>; zero (ALL TERMINALS OPEN); cal0 <pin> (pin at AGND); calv <pin> <known volts>; defaults");
  }
}
void setup() {
  DEV_Module_Init();Wire.setClock(100000);Wire.setTimeOut(20);
  DEV_SET_Backlight(0);LCD_1IN28_Init(HORIZONTAL);
  prefs.begin("tester12vd",false); // Earlier hardware/calibration formats are incompatible.
  for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;zeroRatio[i]=1;}
  if(prefs.getBytesLength("gain")==sizeof(gain)&&prefs.getBytesLength("ratio")==sizeof(zeroRatio)) {
    prefs.getBytes("gain",gain,sizeof(gain));prefs.getBytes("ratio",zeroRatio,sizeof(zeroRatio));
    calibrationMask=prefs.getUShort("mask",0);zeroValid=prefs.getBool("zeroOK",false);
    copiedGainMask=prefs.getUShort("copied",0)&calibrationMask;
    for(int i=0;i<12;i++)if(!std::isfinite(gain[i])||gain[i]<380||gain[i]>480||
      !std::isfinite(zeroRatio[i])||zeroRatio[i]<.97f||zeroRatio[i]>1.03f)zeroValid=false;
    if(!zeroValid){calibrationMask=0;copiedGainMask=0;for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;zeroRatio[i]=1;}}
    calibrated=zeroValid && calibrationMask==0x0fff;
  }
  if(zeroValid&&prefs.getBytesLength("batch")==sizeof(batch)) {
    prefs.getBytes("batch",&batch,sizeof(batch));
    if(!batch.valid())batch=CalibrationBatch{};
  }
  screenStarting=true;screenInitialized=true;renderScreen();DEV_SET_Backlight(80);
  Serial.println("DISPLAY_READY: LIVE_CONNECTOR 240x240, measured pins and voltage");
  delay(350); // Allow isolated power and ADCs to settle before first scan.
  Serial.println("TESTER12V Rev D: real ADC input; + and - indicate relative polarity only");
  Serial.println("CSV: sequence,valid,A1..A12(raw volts),REF0..REF3,state,positive_mask_hex,return_mask_hex,unknown_mask_hex,supply_volts");
}
void loop() {
  serviceCommand();const bool ok=averageRaw(8);
  auto result=tester::classify(corrected,ok);
  if(unstableScan)result.state=tester::State::Ambiguous;
  if(ok&&!calibrated){result={};result.state=tester::State::CalibrationIncomplete;}
  display(result);
  Serial.printf("%lu,%d",sequence++,ok);
  for(int i=0;i<12;i++)if(ok)Serial.printf(",%.6f",raw[i]);else Serial.print(",nan");
  for(int m=0;m<4;m++)if(ok)Serial.printf(",%.6f",reference[m]);else Serial.print(",nan");
  Serial.printf(",%d,%03X,%03X,%03X,%.4f\n",(int)result.state,result.positiveMask,result.returnMask,result.unknownMask,result.volts);
  delay(20);
}
