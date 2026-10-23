#include <cassert>
#include <cstdio>
#include <limits>
#include "../../../firmware/Tester12VRevD/PreviewDetection.h"

using tester::PreviewDetector;
using tester::Result;
static bool window(PreviewDetector &det,Result &out,int scenario=0,bool reverse=false){
  bool ready=false;
  for(int n=0;n<4;n++){
    const float ripple=n&1?1.05f:-1.05f;
    float v[12]={-6.15f+ripple,-6.25f+ripple,.03f,.01f,-.16f,6.15f+ripple,6.25f+ripple};
    if(n==2)v[3]=.55f;
    if(reverse)for(float &x:v)x=-x;
    if(scenario==1&&n==2)v[5]=0;
    if(scenario==2)v[3]=.3f;
    if(scenario==3)v[3]=n&1?.55f:0;
    if(scenario==4&&n==2)v[3]=.9f;
    if(scenario==5)v[5]=11;
    if(scenario==6){v[5]=v[6]=0;}
    if(scenario==7)v[0]=std::numeric_limits<float>::quiet_NaN();
    if(scenario==8&&n==2)v[5]+=4;
    ready=det.push(v,out);
  }
  return ready;
}
int main(){
  PreviewDetector det;Result r;
  assert(!window(det,r));assert(window(det,r));
  assert(r.positiveMask==0x060&&r.returnMask==0x003);
  assert(r.volts>12.3f&&r.volts<12.5f);
  for(int scenario=1;scenario<=8;scenario++){
    det.reset();assert(!window(det,r,scenario));assert(!window(det,r,scenario));assert(!det.ready());
  }
  det.reset();assert(!window(det,r));assert(window(det,r));
  assert(!window(det,r,0,true));assert(!det.ready());
  assert(window(det,r,0,true));assert(r.positiveMask==3&&r.returnMask==0x060);
  det.reset();float open[12]={};
  for(int n=0;n<32;n++)assert(!det.push(open,r));
  assert(!det.ready());assert(!window(det,r));assert(window(det,r));
  det.reset();
  for(int n=0;n<8;n++){
    float v[12]={6.6f,-5.8f};
    const bool ready=det.push(v,r);
    assert(ready==(n==7));
  }
  assert(r.positiveMask==1&&r.returnMask==2&&std::fabs(r.volts-12.4f)<.01f);
  det.reset();
  for(int n=0;n<16;n++){
    float v[12]={6.6f,-3.8f};assert(!det.push(v,r)); // Excess imbalance.
  }
  det.reset();assert(!window(det,r));assert(window(det,r));
  // Ripple can temporarily fail the initial balance test while all known
  // contacts remain energized. Keep the display alive from fresh evidence.
  for(int n=0;n<240;n++){
    float v[12]={-5.8f,-5.9f,.02f,.01f,-.15f,6.6f,6.7f};
    if(n%4==2)v[3]=.55f;
    const bool refreshed=det.push(v,r);
    if(n%4==3)assert(refreshed&&det.ready());
  }
  assert(r.positiveMask==0x060&&r.returnMask==0x003);
  for(int n=0;n<8;n++)assert(!det.push(open,r));
  assert(!det.ready()); // A supply-off window must clear the remembered pair.
  assert(!window(det,r));assert(window(det,r));
  assert(!window(det,r,1));assert(!det.ready()); // A missing pole cannot refresh.
  assert(window(det,r)); // Fresh same-pair evidence can resume without two restarts.
  for(int scenario=0;scenario<4;scenario++){
    det.reset();bool ready=false;
    for(int n=0;n<8;n++){
      float v[12]={};
      if(scenario==0){v[0]=6.f+(n&1?1.05f:-1.05f);v[1]=-v[0];}
      if(scenario==1){for(float &x:v)x=-1;v[0]=11;}
      if(scenario==2){v[0]=4;v[1]=-4;}
      if(scenario==3){v[0]=10;v[1]=-10;}
      ready=det.push(v,r);if(n<7)assert(!ready);
    }
    assert(ready==(scenario<2));
  }
  puts("PASS: noisy pair and four-pin cable detected in eight scans; quiet inputs, spikes, interruptions, reversal, conflicting rails, NaN and range guards checked.");
}
