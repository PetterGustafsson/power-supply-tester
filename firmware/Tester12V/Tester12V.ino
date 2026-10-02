#include "DEV_Config.h"
#include "LCD_1in28.h"
#include "Measurement.h"
#include <Preferences.h>

static UWORD frame[240*240];
UWORD *BlackImage=frame;
static Preferences prefs;
static float gain[12], offset[12], raw[12], corrected[12];
static bool calibrated=false;
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
  float next[12];
  for (uint8_t channel=0;channel<4;channel++) {
    // Single-ended, +/-4.096 V full scale, single shot, 128 SPS, comparator off.
    const uint16_t config=0x8383u|((uint16_t)(4+channel)<<12);
    for (uint8_t bank=0;bank<3;bank++) if (!writeReg(0x48+bank,1,config)) return false;
    const uint32_t began=millis();
    uint8_t complete=0;
    while (complete!=7) {
      if (millis()-began>50) return false;
      for (uint8_t bank=0;bank<3;bank++) {
        if (complete&(1<<bank)) continue;
        uint16_t status,code;
        if (!readReg(0x48+bank,1,status) || (status&0x7fff)!=(config&0x7fff)) return false;
        if (!(status&0x8000)) continue;
        if (!readReg(0x48+bank,0,code)) return false;
        const float volts=(int16_t)code*0.000125f;
        // Normal operation stays well inside these bounds, even at 48 V.
        if (!std::isfinite(volts) || volts<0.15f || volts>3.10f) return false;
        next[bank*4+channel]=volts;complete|=(1<<bank);
      }
      if (complete!=7) delay(1);
    }
  }
  memcpy(raw,next,sizeof(raw));
  for(int i=0;i<12;i++) corrected[i]=raw[i]*gain[i]+offset[i];
  return true;
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
 {'.',{0,0,0,0,0,12,12}},{'/',{1,2,2,4,8,8,16}}
};
void pixel(int x,int y,uint16_t color) {
  if(x<0||x>=240||y<0||y>=240)return;
  frame[y*240+x]=(color>>8)|(color<<8); // LCD expects big-endian RGB565 bytes.
}
void text(const char *s,int y,int scale,uint16_t color) {
  int x=(240-(int)strlen(s)*6*scale+scale)/2;
  for(;*s;s++,x+=6*scale) for(const auto &g:font) if(g.c==*s) {
    for(int row=0;row<7;row++)for(int col=0;col<5;col++)if(g.rows[row]&(16>>col))
      for(int yy=0;yy<scale;yy++)for(int xx=0;xx<scale;xx++)pixel(x+col*scale+xx,y+row*scale+yy,color);
    break;
  }
}
void display(const tester::Result &r) {
  memset(frame,0,sizeof(frame));
  const uint16_t cyan=0x7EFF,amber=0xFEA0,red=0xF986,gray=0x7BEF,white=0xFFFF;
  text("12 V TESTER",32,2,cyan);
  char line[32];
  switch(r.state) {
    case tester::State::Pair:
      snprintf(line,sizeof(line),"%.2f V",r.volts);text(line,80,3,white);
      snprintf(line,sizeof(line),"+%d  -%d",r.positive+1,r.negative+1);text(line,117,2,amber);
      text(r.nominal12?"12 V RANGE":"CHECK VOLTAGE",153,1,r.nominal12?0x07E0:amber);break;
    case tester::State::NoPair:text("NO LIVE PAIR",94,2,gray);break;
    case tester::State::Ambiguous:text("MULTI / CHECK",94,2,amber);break;
    case tester::State::OverRange:text("OVER RANGE",91,2,red);text("ABOVE 18 V",123,2,red);break;
    case tester::State::CalibrationIncomplete:text("FINISH CAL",94,2,amber);text("ALL 12 CHANNELS",128,1,gray);break;
    default:text("ADC FAULT",94,2,red);text("CHECK POWER / I2C",128,1,amber);break;
  }
  text(calibrated?"CAL LOADED":(calibrationMask?"PARTIAL CAL":"UNCALIBRATED"),183,1,gray);
  LCD_1IN28_Display(frame);
}
void serviceCommand() {
  while(Serial.available()) {
    char c=Serial.read();
    if(c=='\r')continue;
    if(c!='\n') { if(commandLength<sizeof(command)-1)command[commandLength++]=c;else commandLength=0;continue; }
    command[commandLength]=0;commandLength=0;
    int pin;float g,o;
    if(sscanf(command,"cal %d %f %f",&pin,&g,&o)==3 && pin>=1 && pin<=12 &&
       std::isfinite(g)&&std::isfinite(o)&&g>30&&g<45&&fabsf(o)<100) {
      gain[pin-1]=g;offset[pin-1]=o;
      prefs.putBytes("gain",gain,sizeof(gain));prefs.putBytes("offset",offset,sizeof(offset));
      calibrationMask|=1u<<(pin-1);prefs.putUShort("mask",calibrationMask);
      calibrated=calibrationMask==0x0fff;Serial.printf("CAL_SAVED pin=%d gain=%.7f offset=%.7f\n",pin,g,o);
    } else if(strcmp(command,"defaults")==0) {
      for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;offset[i]=0;}
      prefs.clear();calibrationMask=0;calibrated=false;Serial.println("CAL_CLEARED");
    } else Serial.println("COMMANDS: cal <1..12> <gain> <offset>; defaults");
  }
}
void setup() {
  DEV_Module_Init();Wire.setClock(100000);Wire.setTimeOut(20);
  DEV_SET_Backlight(0);LCD_1IN28_Init(HORIZONTAL);
  prefs.begin("tester12v",false);
  for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;offset[i]=0;}
  if(prefs.getBytesLength("gain")==sizeof(gain)&&prefs.getBytesLength("offset")==sizeof(offset)) {
    prefs.getBytes("gain",gain,sizeof(gain));prefs.getBytes("offset",offset,sizeof(offset));
    calibrationMask=prefs.getUShort("mask",0);calibrated=true;
    for(int i=0;i<12;i++)if(!std::isfinite(gain[i])||gain[i]<30||gain[i]>45||!std::isfinite(offset[i])||fabsf(offset[i])>=100) calibrated=false;
    if(!calibrated || !calibrationMask){calibrationMask=0;for(int i=0;i<12;i++){gain[i]=tester::kNominalGain;offset[i]=0;}}
    calibrated=calibrationMask==0x0fff;
  }
  display({tester::State::AdcFault,-1,-1,0,false});DEV_SET_Backlight(80);
  delay(350); // Supervisor release plus reference/filter settling.
  Serial.println("TESTER12V Rev A: real ADC input; + and - indicate relative polarity only");
  Serial.println("CSV: sequence,valid,A1..A12(volts),state,positive,negative,pair_volts");
}
void loop() {
  serviceCommand();const bool ok=acquire();
  auto result=tester::classify(corrected,ok);
  if(ok && calibrationMask && !calibrated) result={tester::State::CalibrationIncomplete,-1,-1,0,false};
  display(result);
  Serial.printf("%lu,%d",sequence++,ok);
  for(int i=0;i<12;i++)if(ok)Serial.printf(",%.6f",raw[i]);else Serial.print(",nan");
  Serial.printf(",%d,%d,%d,%.4f\n",(int)result.state,result.positive+1,result.negative+1,result.volts);
  delay(20);
}
