#include "../../../firmware/Tester12VRevD/Measurement.h"
#include <cassert>
#include <cstdio>
#include <limits>
#include <cmath>
#include <initializer_list>
extern "C" int check_batch(int count,const float *raw,const float *ref,const float *ratio,const float *gain,
                          const unsigned short *pos,const unsigned short *neg,float known,float tolerance,float *maxError) {
  float v[12];*maxError=0;
  for(int n=0;n<count;n++) {
    if(!tester::normalize(raw+12*n,ref+4*n,ratio,gain,v))return n+1;
    auto r=tester::classify(v,true);
    bool live=pos[n]&&neg[n];
    if(live) {
      if((r.state!=tester::State::Supply&&r.state!=tester::State::OverRange)||r.positiveMask!=pos[n]||r.returnMask!=neg[n])return n+1;
      *maxError=fmaxf(*maxError,fabsf(r.volts-known));
      if(fabsf(r.volts-known)>tolerance)return n+1;
    } else if(r.state!=tester::State::NoVoltage||r.unknownMask!=tester::kAllPins)return n+1;
  }
  return 0;
}
int main() {
  float raw[12],ref[4],ratio[12],gain[12],v[12];unsigned long cases=0;
  for(int i=0;i<12;i++){ratio[i]=1+(i-5.5f)*.0001f;gain[i]=tester::kNominalGain*(1+(i-5.5f)*.0003f);}
  for(unsigned code=0;code<531441;code++) {
    int state[12],np=0,nn=0;uint16_t pos=0,neg=0;unsigned c=code;
    for(int i=0;i<12;i++){state[i]=c%3;c/=3;if(state[i]==1){np++;pos|=1<<i;}if(state[i]==2){nn++;neg|=1<<i;}}
    for(float volts:{9.f,12.f,17.9f})for(float rail:{.5f,.58f,.66f}) {
      for(int m=0;m<4;m++)ref[m]=rail+m*.0002f;
      for(int i=0;i<12;i++) {
        float delta=0;
        if(np&&nn)delta=state[i]==1?volts*nn/(np+nn):state[i]==2?-volts*np/(np+nn):0;
        raw[i]=ratio[i]*ref[i%4]+delta/gain[i];
      }
      assert(tester::normalize(raw,ref,ratio,gain,v));auto r=tester::classify(v,true);
      if(np&&nn){assert(r.state==tester::State::Supply);assert(r.positiveMask==pos&&r.returnMask==neg);assert(fabsf(r.volts-volts)<.001f);}
      else assert(r.state==tester::State::NoVoltage&&r.unknownMask==tester::kAllPins);
      cases++;
    }
  }
  for(int i=0;i<12;i++)v[i]=0;v[0]=6;v[1]=-6;v[2]=3;
  auto bad=tester::classify(v,true);assert(bad.state==tester::State::Ambiguous&&bad.unknownMask==tester::kAllPins);
  v[2]=.26f;assert(tester::classify(v,true).state==tester::State::Ambiguous);
  v[2]=0;v[0]=12;v[1]=-12;assert(tester::classify(v,true).state==tester::State::OverRange);
  assert(tester::classify(v,false).state==tester::State::AdcFault);
  v[0]=std::numeric_limits<float>::quiet_NaN();assert(tester::classify(v,true).state==tester::State::AdcFault);
  ref[0]=0;assert(!tester::normalize(raw,ref,ratio,gain,v));ref[0]=.58f;
  ratio[0]=0;assert(!tester::normalize(raw,ref,ratio,gain,v));ratio[0]=1;
  gain[0]=37.3f;assert(!tester::normalize(raw,ref,ratio,gain,v));
  printf("PASS: %lu ideal assignment/voltage/reference cases (all 531441 pin assignments); fault, ambiguity, invalid reference and legacy calibration tests.\n",cases);
}
