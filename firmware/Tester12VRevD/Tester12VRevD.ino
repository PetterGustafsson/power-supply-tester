#include "DEV_Config.h"
#include "LCD_1in28.h"
#include "Measurement.h"
#include <Preferences.h>

static UWORD frame[240*240];
UWORD *BlackImage=frame;
static Preferences prefs;
static float gain[12], zeroRatio[12], raw[12], reference[4], corrected[12];
static bool calibrated=false, zeroValid=false;
static bool unstableScan=false;
static int pendingPin=-1;
static float pendingLow=0;
static uint16_t calibrationMask=0;
static uint32_t sequence=0;
static char command[96];
static unsigned commandLength=0;

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

// Compact 5x7 font: digits, capitals and the signs used on the round LCD.
struct Glyph { char c; uint8_t rows[7]; };
static const Glyph font[]={
 {'0',{14,17,19,21,25,17,14}},{'1',{4,12,4,4,4,4,14}},
 {'2',{14,17,1,2,4,8,31}},{'3',{30,1,1,14,1,1,30}},
 {'4',{2,6,10,18,31,2,2}},{'5',{31,16,16,30,1,1,30}},
 {'6',{14,16,16,30,17,17,14}},{'7',{31,1,2,4,8,8,8}},
 {'8',{14,17,17,14,17,17,14}},{'9',{14,17,17,15,1,1,14}},
 {'A',{14,17,17,31,17,17,17}},{'B',{30,17,17,30,17,17,30}},
 {'C',{14,17,16,16,16,17,14}},{'D',{30,17,17,17,17,17,30}},
 {'E',{31,16,16,30,16,16,31}},{'F',{31,16,16,30,16,16,16}},
 {'G',{14,17,16,23,17,17,15}},{'H',{17,17,17,31,17,17,17}},
 {'I',{14,4,4,4,4,4,14}},{'J',{7,2,2,2,2,18,12}},
 {'K',{17,18,20,24,20,18,17}},{'L',{16,16,16,16,16,16,31}},
 {'M',{17,27,21,21,17,17,17}},{'N',{17,25,21,19,17,17,17}},
 {'O',{14,17,17,17,17,17,14}},{'P',{30,17,17,30,16,16,16}},
 {'Q',{14,17,17,17,21,18,13}},{'R',{30,17,17,30,20,18,17}},
 {'S',{15,16,16,14,1,1,30}},{'T',{31,4,4,4,4,4,4}},
 {'U',{17,17,17,17,17,17,14}},{'V',{17,17,17,17,17,10,4}},
 {'W',{17,17,17,21,21,21,10}},{'X',{17,17,10,4,10,17,17}},
 {'Y',{17,17,10,4,4,4,4}},{'Z',{31,1,2,4,8,16,31}},
 {'+',{0,4,4,31,4,4,0}},{'-',{0,0,0,31,0,0,0}},
 {'?',{14,17,1,2,4,0,4}},
 {'.',{0,0,0,0,0,12,12}},{'/',{1,2,2,4,8,8,16}}
};
void pixel(int x,int y,uint16_t color) {
  if(x<0||x>=240||y<0||y>=240)return;
  frame[y*240+x]=(color>>8)|(color<<8); // LCD expects big-endian RGB565 bytes.
}
void textAt(const char *s,int x,int y,int scale,uint16_t color) {
  for(;*s;s++,x+=6*scale)for(const auto &g:font)if(g.c==*s) {
    for(int row=0;row<7;row++)for(int col=0;col<5;col++)if(g.rows[row]&(16>>col))
      for(int yy=0;yy<scale;yy++)for(int xx=0;xx<scale;xx++)pixel(x+col*scale+xx,y+row*scale+yy,color);
    break;
  }
}
void text(const char *s,int y,int scale,uint16_t color) {
  textAt(s,(240-(int)strlen(s)*6*scale+scale)/2,y,scale,color);
}
void display(const tester::Result &r) {
  memset(frame,0,sizeof(frame));
  const uint16_t cyan=0x7EFF,amber=0xFEA0,red=0xF986,gray=0x9CF3,white=0xFFFF;
  text("12 V PIN TESTER",23,1,cyan);char line[32];
  if(r.state==tester::State::CalibrationIncomplete||r.state==tester::State::AdcFault) {
    text(r.state==tester::State::AdcFault?"ADC FAULT":"FINISH CAL",83,2,amber);
    text(r.state==tester::State::AdcFault?"CHECK POWER / I2C":"ALL 12 CHANNELS",119,1,gray);
    text(calibrated?"CAL LOADED":"CAL REQUIRED",175,1,gray);
  } else {
    if(r.state==tester::State::Supply||r.state==tester::State::OverRange) {
      snprintf(line,sizeof(line),"%.2f V",r.volts);text(line,47,3,r.state==tester::State::OverRange?red:white);
    } else text(r.state==tester::State::NoVoltage?"NO LIVE VOLTAGE":"CHECK WIRING",53,2,amber);
    for(int i=0;i<12;i++) {
      char mark=(r.positiveMask&(1u<<i))?'+':(r.returnMask&(1u<<i))?'-':'?';
      snprintf(line,sizeof(line),"%02d %c",i+1,mark);
      textAt(line,33+(i%3)*64,88+(i/3)*25,2,mark=='+'?amber:mark=='-'?cyan:gray);
    }
    text(r.state==tester::State::OverRange?"ABOVE 18 V":"? OPEN / UNKNOWN",193,1,r.state==tester::State::OverRange?red:gray);
    text("ONE SUPPLY ONLY",213,1,gray);
  }
  LCD_1IN28_Display(frame);
}
// Calibration takes explicit serial commands and a known voltage source.
// Never automatically zero with an unknown DUT attached.
bool averageRaw(unsigned count=32) {
  double sum[12]={0},refSum[4]={0};float low[12],high[12];unstableScan=false;
  for(unsigned n=0;n<count;n++) {
    if(!acquire())return false;
    for(int i=0;i<12;i++) {
      sum[i]+=raw[i];float sample=(raw[i]-zeroRatio[i]*reference[i%4])*gain[i];
      if(n==0)low[i]=high[i]=sample;else{low[i]=fminf(low[i],sample);high[i]=fmaxf(high[i],sample);}
    }
    for(int m=0;m<4;m++)refSum[m]+=reference[m];
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
  calibrated=zeroValid && calibrationMask==0x0fff;
}
void serviceCommand() {
  while(Serial.available()) {
    char c=Serial.read();if(c=='\r')continue;
    if(c!='\n'){if(commandLength<sizeof(command)-1)command[commandLength++]=c;else commandLength=0;continue;}
    command[commandLength]=0;commandLength=0;
    int pin;float known;
    if(strcmp(command,"zero")==0) {
      if(!averageRaw(64)){Serial.println("CAL_ERROR acquisition");continue;}
      float lo=raw[0],hi=raw[0];for(float v:raw){lo=fminf(lo,v);hi=fmaxf(hi,v);}
      if(hi-lo>.004f){Serial.println("CAL_ERROR disconnect ALL test leads before zero");continue;}
      bool ratiosOK=true;for(int i=0;i<12;i++){float r=raw[i]/reference[i%4];if(r<.97f||r>1.03f)ratiosOK=false;}
      if(!ratiosOK){Serial.println("CAL_ERROR reference mismatch");continue;}
      for(int i=0;i<12;i++)zeroRatio[i]=raw[i]/reference[i%4];zeroValid=true;pendingPin=-1;saveCalibration();
      Serial.println("ZERO_SAVED; this assumes all twelve terminals were open");
    } else if(sscanf(command,"cal0 %d",&pin)==1 && pin>=1 && pin<=12 && zeroValid) {
      if(!averageRaw(64)){Serial.println("CAL_ERROR acquisition");continue;}
      pendingPin=pin-1;pendingLow=corrected[pendingPin]/gain[pendingPin];
      Serial.printf("CAL_LOW_SAVED pin=%d; apply known +12V relative to AGND, then calv %d 12.000\n",pin,pin);
    } else if(sscanf(command,"calv %d %f",&pin,&known)==2 && pin>=1 && pin<=12 &&
              pendingPin==pin-1 && std::isfinite(known) && known>10 && known<14 && zeroValid) {
      if(!averageRaw(64)){Serial.println("CAL_ERROR acquisition");continue;}
      float delta=corrected[pin-1]/gain[pin-1]-pendingLow;
      float g=known/delta;
      if(!std::isfinite(g)||g<380||g>480){Serial.println("CAL_ERROR check applied voltage and wiring");continue;}
      gain[pin-1]=g;calibrationMask|=1u<<(pin-1);pendingPin=-1;saveCalibration();
      Serial.printf("CAL_SAVED pin=%d gain=%.7f mask=%03X\n",pin,g,calibrationMask);
    } else if(strcmp(command,"defaults")==0) {
      for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;zeroRatio[i]=1;}
      prefs.clear();calibrationMask=0;zeroValid=false;calibrated=false;pendingPin=-1;Serial.println("CAL_CLEARED");
    } else Serial.println("COMMANDS: zero (ALL TERMINALS OPEN); cal0 <pin> (pin at AGND); calv <pin> <known volts>; defaults");
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
    for(int i=0;i<12;i++)if(!std::isfinite(gain[i])||gain[i]<380||gain[i]>480||
      !std::isfinite(zeroRatio[i])||zeroRatio[i]<.97f||zeroRatio[i]>1.03f)zeroValid=false;
    if(!zeroValid){calibrationMask=0;for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;zeroRatio[i]=1;}}
    calibrated=zeroValid && calibrationMask==0x0fff;
  }
  display({});DEV_SET_Backlight(80);
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
