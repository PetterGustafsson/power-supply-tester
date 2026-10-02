#include "../../../firmware/Tester12VRevC/Measurement.h"
#include <cassert>
#include <cstdio>
#include <limits>
int main(){
 float raw[12],zero[12],gain[12],v[12];int cases=0;
 for(int i=0;i<12;i++){zero[i]=.578f*(1+(i-5.5f)*.0002f);gain[i]=tester::kNominalGain;}
 for(int a=0;a<12;a++)for(int b=0;b<12;b++)if(a!=b){
  for(float scale:{.85f,1.f,1.15f})for(float volts:{0.f,1.f,3.3f,5.f,9.f,12.f,15.f,17.9f,24.f}){
   for(int i=0;i<12;i++)raw[i]=zero[i]*scale;
   raw[a]+=volts/(2*gain[a]);raw[b]-=volts/(2*gain[b]);
   assert(tester::normalize(raw,zero,gain,v));auto r=tester::classify(v,true);
   if(volts==0)assert(r.state==tester::State::NoPair);
   else if(volts>18)assert(r.state==tester::State::OverRange);
   else{assert(r.state==tester::State::Pair);assert(r.positive==a&&r.negative==b);assert(fabs(r.volts-volts)<.001);}
   cases++;
  }
 }
 for(int i=0;i<12;i++)raw[i]=zero[i];
 raw[0]+=.014;raw[1]-=.014;raw[2]+=.008;
 assert(tester::normalize(raw,zero,gain,v));assert(tester::classify(v,true).state==tester::State::Ambiguous);
 assert(tester::classify(v,false).state==tester::State::AdcFault);
 raw[0]=std::numeric_limits<float>::quiet_NaN();assert(!tester::normalize(raw,zero,gain,v));raw[0]=zero[0];
 zero[0]=0;assert(!tester::normalize(raw,zero,gain,v));zero[0]=.578;
 gain[0]=37.3;assert(!tester::normalize(raw,zero,gain,v));
 printf("PASS: %d ordered-pair/voltage/bias cases; multiple sources, acquisition failure, invalid baseline, NaN and legacy gain rejected.\n",cases);
}
