"""Run the real firmware command parser with serial/NVS/ADC hardware stubs.

Only acquisition and transport are stubbed; serviceCommand and save/status logic
are extracted unchanged from the sketch. This test never opens a USB device.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[3]
firmware=ROOT/'firmware/Tester12VRevD'
source=(firmware/'Tester12VRevD.ino').read_text()
commands=source[source.index('void saveCalibration()'):source.index('void setup()')]
harness=r'''
#include "CalibrationBatch.h"
#include "Measurement.h"
#include <cassert>
#include <cstring>
#include <string>
#include <map>
#include <vector>
#include <cstdarg>
#include <cstdio>
#include <limits>
struct FakePreferences {
  std::map<std::string,std::vector<unsigned char>> data;
  size_t putBytes(const char* k,const void* v,size_t n) {
    auto p=static_cast<const unsigned char*>(v);data[k]={p,p+n};return n;
  }
  void putBool(const char* k,bool v){putBytes(k,&v,sizeof(v));}
  void putUShort(const char* k,uint16_t v){putBytes(k,&v,sizeof(v));}
  void clear(){data.clear();}
} prefs;
struct FakeSerial {
  std::string input,output;
  bool available(){return !input.empty();}
  char read(){char c=input[0];input.erase(0,1);return c;}
  void println(const char* s){output+=s;output+='\n';}
  void printf(const char* fmt,...) {
    char b[512];va_list a;va_start(a,fmt);vsnprintf(b,sizeof(b),fmt,a);va_end(a);output+=b;
  }
} Serial;
static float gain[12],zeroRatio[12],raw[12],reference[4],corrected[12];
static bool calibrated=false,zeroValid=true,acquisitionOK=true;
static uint16_t calibrationMask=3,copiedGainMask=0;
static CalibrationBatch batch;
static char command[96];static unsigned commandLength=0;
bool averageRaw(unsigned){return acquisitionOK;}
'''
checks=r'''
std::string send(std::string line){Serial.input=line+"\n";Serial.output.clear();serviceCommand();return Serial.output;}
int main(){
  for(int i=0;i<12;i++){gain[i]=427.f+i*.01f;zeroRatio[i]=1;}
  const float oldGain=gain[0];
  assert(send("calbegin A1234567").find("protocol=2 batch=A1234567")!=std::string::npos);
  assert(gain[0]==oldGain&&zeroValid&&calibrationMask==3);
  for(int i=0;i<12;i++){
    corrected[i]=(-.001f-i*.00002f)*gain[i];
    assert(send("cal0 "+std::to_string(i+1)).find("CAL_LOW_SAVED")!=std::string::npos);
  }
  assert(batch.lowMask==0xfff&&batch.doneMask==0);
  // Simulate boot restoration from the exact NVS blob after all twelve zeros.
  auto blob=prefs.data["batch"];batch=CalibrationBatch{};
  assert(blob.size()==sizeof(batch));memcpy(&batch,blob.data(),sizeof(batch));assert(batch.valid());
  for(int i=0;i<12;i++){
    const float expected=420.f+i;
    corrected[i]=(batch.low[i]+12.f/expected)*gain[i];
    assert(send("calv "+std::to_string(i+1)+" 12.000").find("CAL_SAVED")!=std::string::npos);
    assert(std::fabs(gain[i]-expected)<.001f);
  }
  assert(batch.doneMask==0xfff&&calibrationMask==0xfff&&calibrated);
  assert(send("calstatus").find("low_mask=FFF done_mask=FFF mask=FFF zero=1")!=std::string::npos);
  const float calibratedGain=gain[0];
  assert(send("calbegin B1234567").find("low_mask=000 done_mask=000 mask=FFF")!=std::string::npos);
  assert(gain[0]==calibratedGain&&zeroValid);
  assert(send("calv 1 12.00").find("CAL_SAVED")==std::string::npos);
  corrected[0]=0;
  assert(send("cal0 1").find("CAL_ERROR")!=std::string::npos);assert(batch.lowMask==0);
  corrected[0]=-.0013f*gain[0];acquisitionOK=false;
  assert(send("cal0 1").find("CAL_ERROR acquisition")!=std::string::npos);assert(batch.lowMask==0);
  acquisitionOK=true;assert(send("cal0 1").find("CAL_LOW_SAVED")!=std::string::npos);
  // Copy only from a measured input; leave all individual baseline ratios intact.
  calibrationMask=1;gain[0]=427.93158f;zeroRatio[4]=1.0002f;
  assert(send("calcopy 1").find("CAL_COPIED source=1")!=std::string::npos);
  assert(calibrated&&calibrationMask==0xfff&&copiedGainMask==0xffe);
  for(float g:gain)assert(g==gain[0]);assert(zeroRatio[4]==1.0002f);
  uint16_t persistedCopied=0;memcpy(&persistedCopied,prefs.data["copied"].data(),2);assert(persistedCopied==0xffe);
  assert(send("calcopy 2").find("CAL_COPIED")==std::string::npos);
  assert(send("calcopy 0").find("CAL_COPIED")==std::string::npos);
  zeroValid=false;assert(send("calcopy 1").find("CAL_COPIED")==std::string::npos);zeroValid=true;
  const auto before=batch;
  assert(send("calv 1 nan").find("CAL_SAVED")==std::string::npos);
  assert(send("calv 1 10").find("CAL_SAVED")==std::string::npos);
  assert(send("calv 1 14").find("CAL_SAVED")==std::string::npos);
  assert(batch.lowMask==before.lowMask&&batch.doneMask==before.doneMask);
  batch.low[0]=std::numeric_limits<float>::quiet_NaN();assert(!batch.valid());
  batch=before;batch.format=0;assert(!batch.valid());
  batch=before;batch.doneMask=2;assert(!batch.valid());
  batch=before;batch.lowMask=0x8000;assert(!batch.valid());
  puts("PASS: real command parser; all 12 lows before highs, NVS round-trip, per-pin gains, new-pass preservation and invalid captures.");
}
'''
with tempfile.TemporaryDirectory() as temp:
    cpp=Path(temp)/'commands.cpp';cpp.write_text(harness+commands+checks)
    binary=Path(temp)/'commands'
    subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-I',str(firmware),str(cpp),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
