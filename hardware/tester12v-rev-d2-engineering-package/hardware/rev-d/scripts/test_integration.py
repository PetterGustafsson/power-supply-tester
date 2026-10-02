"""Host-run the actual sketch with mocked I2C/serial/storage/LCD hardware.
Only hardware includes are replaced; acquisition/calibration/display code is
compiled directly from the delivered sketch. This is not a physical test.
"""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1];FW=ROOT.parents[1]/'firmware/Tester12VRevD'
s=(FW/'Tester12VRevD.ino').read_text()
for line in ('#include "DEV_Config.h"','#include "LCD_1in28.h"','#include <Preferences.h>'):s=s.replace(line,'')
s=s.replace('#include "Measurement.h"','#include "'+str(FW/'Measurement.h')+'"')
stubs=r'''
#include <cstdint>
#include <cstring>
#include <cmath>
#include <cassert>
#include <cstdio>
#include <cstdarg>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
using UWORD=uint16_t;
static uint32_t ticks=0;
uint32_t millis(){return ticks++;}
void delay(unsigned x){ticks+=x;}
void DEV_Module_Init(){}
void DEV_SET_Backlight(int){}
const int HORIZONTAL=0;
void LCD_1IN28_Init(int){}
static std::string imageFile;
void LCD_1IN28_Display(uint16_t *frame){
 if(imageFile.empty())return;
 std::ofstream f(imageFile,std::ios::binary);f<<"P6\n240 240\n255\n";
 for(int i=0;i<240*240;i++){
  uint16_t v=(frame[i]>>8)|(frame[i]<<8);char rgb[3]={char(((v>>11)&31)*255/31),char(((v>>5)&63)*255/63),char((v&31)*255/31)};f.write(rgb,3);
 }
}
struct MockSerial {
 std::string input,output;
 int available(){return input.size();}
 char read(){char c=input[0];input.erase(0,1);return c;}
 void println(const char*s){output+=s;output+='\n';}
 void print(const char*s){output+=s;}
 void printf(const char *fmt,...){char b[512];va_list a;va_start(a,fmt);vsnprintf(b,sizeof(b),fmt,a);va_end(a);output+=b;}
} Serial;
struct Preferences {
 std::map<std::string,std::vector<uint8_t>> data;
 void begin(const char*,bool){}
 void clear(){data.clear();}
 size_t putBytes(const char*k,const void*v,size_t n){const auto*p=(const uint8_t*)v;data[k]={p,p+n};return n;}
 size_t getBytesLength(const char*k){return data[k].size();}
 size_t getBytes(const char*k,void*v,size_t n){auto&a=data[k];size_t m=std::min(n,a.size());memcpy(v,a.data(),m);return m;}
 void putBool(const char*k,bool v){putBytes(k,&v,sizeof(v));}
 void putUShort(const char*k,uint16_t v){putBytes(k,&v,sizeof(v));}
 bool getBool(const char*k,bool v){if(getBytesLength(k)==sizeof(v))getBytes(k,&v,sizeof(v));return v;}
 uint16_t getUShort(const char*k,uint16_t v){if(getBytesLength(k)==sizeof(v))getBytes(k,&v,sizeof(v));return v;}
};
struct MockWire {
 uint8_t address=0,reg[4]={0};std::vector<uint8_t> tx,rx;size_t cursor=0;
 uint16_t cfg[4]={0},writes[4]={0};float nodes[4][4];int missing=-1;bool busy=false,corrupt=false,changing=false;
 void setClock(int){}void setTimeOut(int){}
 void beginTransmission(uint8_t a){address=a;tx.clear();}
 void write(uint8_t v){tx.push_back(v);}
 uint8_t endTransmission(bool=true){int b=address-0x48;if(b<0||b>3||b==missing)return 2;
  if(!tx.empty())reg[b]=tx[0];
  if(tx.size()==3){cfg[b]=(tx[1]<<8)|tx[2];writes[b]++;}
  return 0;
 }
 uint8_t requestFrom(uint8_t a,uint8_t n){int b=a-0x48;if(b<0||b>3||b==missing)return 0;
  uint16_t v;
  if(reg[b]==1)v=cfg[b]^(corrupt?2:0);else{
   int mux=((cfg[b]>>12)&7)-4;assert(mux>=0&&mux<4);
   float x=nodes[b][mux];if(changing&&b==0&&mux==0&&writes[0]%8>=4)x+=.006;
   v=(int16_t)lround(x/.00003125f);
  }
  if(reg[b]==1&&busy)v&=0x7fff;
  rx={uint8_t(v>>8),uint8_t(v)};cursor=0;return n;
 }
 int read(){return rx.at(cursor++);}
} Wire;
'''
tests=r'''
static void baseline(){for(auto &bank:Wire.nodes)for(float &v:bank)v=.578125f;}
static void commandLine(const std::string&s){Serial.input=s+"\n";serviceCommand();}
int main(int argc,char **argv){
 assert(argc==2);std::string dir=argv[1];baseline();setup();
 assert(!calibrated&&averageRaw(8));
 for(int b=0;b<4;b++)assert(Wire.writes[b]>0);
 assert((Wire.cfg[3]&0x7fff)==(0xc783&0x7fff));
 Wire.missing=3;assert(!acquire());Wire.missing=-1;
 Wire.busy=true;assert(!acquire());Wire.busy=false;
 Wire.corrupt=true;assert(!acquire());Wire.corrupt=false;
 Wire.nodes[3][0]=.2f;assert(!acquire());baseline();
 commandLine("zero");assert(zeroValid&&!calibrated);
 for(int pin=1;pin<=12;pin++){
  baseline();Wire.nodes[(pin-1)/4][(pin-1)%4]=.578125f-.578125f/tester::kNominalGain;
  commandLine("cal0 "+std::to_string(pin));assert(pendingPin==pin-1);
  Wire.nodes[(pin-1)/4][(pin-1)%4]=.578125f+(12-.578125f)/tester::kNominalGain;
  commandLine("calv "+std::to_string(pin)+" 12.000");assert(calibrationMask&(1u<<(pin-1)));
 }
 assert(calibrated&&calibrationMask==0xfff);baseline();setup();assert(calibrated);
 // One positive and eleven returns: no open DUT reference is available.
 for(int i=0;i<12;i++)Wire.nodes[i/4][i%4]=.578125f+(i==0?11.f:-1.f)/gain[i];
 assert(averageRaw(8));auto result=tester::classify(corrected,true);
 assert(result.state==tester::State::Supply&&result.positiveMask==1&&result.returnMask==0xffe);
 imageFile=dir+"/display-all-connected.ppm";display(result);
 Wire.changing=true;assert(!averageRaw(8)&&unstableScan);Wire.changing=false;
 baseline();assert(averageRaw(8));result=tester::classify(corrected,true);
 assert(result.state==tester::State::NoVoltage&&result.unknownMask==0xfff);
 imageFile=dir+"/display-no-voltage.ppm";display(result);
 Wire.missing=3;imageFile=dir+"/display-adc-fault.ppm";loop();
 assert(Serial.output.find(",nan,nan")!=std::string::npos);Wire.missing=-1;
 commandLine("defaults");assert(!calibrated&&!zeroValid&&calibrationMask==0);
 puts("PASS: actual sketch acquisition uses all four ADCs; absent reference ADC, timeout, config corruption, invalid reference, serial calibration of all 12 pins, persisted calibration, 1-plus/11-return classification, changing-input rejection, no-voltage and fault display checked.");
}
'''
source=Path('/private/tmp/tester12vd-integration.cpp');source.write_text(stubs+'\n'+s+'\n'+tests)
exe=Path('/private/tmp/tester12vd-integration')
r=subprocess.run(['clang++','-std=c++17','-O2',str(source),'-o',str(exe)],capture_output=True,text=True);assert r.returncode==0,r.stderr
r=subprocess.run([str(exe),str(ROOT/'previews')],capture_output=True,text=True)
(ROOT/'validation/firmware-integration.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
from PIL import Image
for file in (ROOT/'previews').glob('display-*.ppm'):
 im=Image.open(file);im.save(file.with_suffix('.png'));file.unlink()
print(r.stdout)
