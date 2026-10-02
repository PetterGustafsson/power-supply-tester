#pragma once
#include <cmath>
#include <cstdint>
namespace tester {
constexpr int kInputs=12;
constexpr uint16_t kAllPins=0x0fff;
constexpr float kNominalGain=1.f+2000000.f/4700.f;
// U8 measures a replica open channel each mux phase. No DUT pin is presumed open.
inline bool normalize(const float *raw,const float *reference,const float *zeroRatio,const float *gain,float *out) {
  for(int m=0;m<4;m++)if(!std::isfinite(reference[m])||reference[m]<.35f||reference[m]>.85f)return false;
  for(int i=0;i<kInputs;i++) {
    if(!std::isfinite(raw[i])||raw[i]<.20f||raw[i]>.98f||
       !std::isfinite(zeroRatio[i])||zeroRatio[i]<.97f||zeroRatio[i]>1.03f||
       !std::isfinite(gain[i])||gain[i]<380||gain[i]>480)return false;
    out[i]=(raw[i]-zeroRatio[i]*reference[i%4])*gain[i];
  }
  return true;
}
enum class State { NoVoltage, Supply, Ambiguous, OverRange, AdcFault, CalibrationIncomplete };
struct Result {
  State state=State::AdcFault;
  uint16_t positiveMask=0,returnMask=0,unknownMask=kAllPins;
  float volts=0;
  bool nominal12=false;
};
// One common supply with any count of positive, return and open pins.
// Unknown does not prove an open circuit, continuity, earth or a dead pin.
inline Result classify(const float *v,bool acquisitionOK) {
  Result r;if(!acquisitionOK)return r;
  float lo=v[0],hi=v[0],sum=0;
  for(int i=0;i<kInputs;i++) {
    if(!std::isfinite(v[i]))return r;
    lo=fminf(lo,v[i]);hi=fmaxf(hi,v[i]);sum+=v[i];
  }
  r.volts=hi-lo;
  if(r.volts<.5f){r.state=fabsf(sum/12.f)<=.20f?State::NoVoltage:State::Ambiguous;return r;}
  uint16_t pos=0,neg=0;int np=0,nn=0;float sp=0,sn=0;
  r.state=State::Ambiguous;
  for(int i=0;i<kInputs;i++) {
    if(v[i]>.35f){pos|=1u<<i;np++;sp+=v[i];}
    else if(v[i]<-.35f){neg|=1u<<i;nn++;sn+=v[i];}
    else if(fabsf(v[i])>.20f)return r;
  }
  if(!np||!nn)return r;
  const float vp=sp/np,vn=sn/nn;
  for(int i=0;i<kInputs;i++) {
    if((pos&(1u<<i))&&fabsf(v[i]-vp)>.25f)return r;
    if((neg&(1u<<i))&&fabsf(v[i]-vn)>.25f)return r;
  }
  // Equal nominal input impedances provide a useful consistency check,
  // with resistor tolerance allowed. This cannot prove external topology.
  if(fabsf((sp+sn)/(np+nn))>fmaxf(.20f,(vp-vn)*.02f))return r;
  r.volts=vp-vn;r.positiveMask=pos;r.returnMask=neg;r.unknownMask=kAllPins&~(pos|neg);
  r.nominal12=r.volts>=10.8f&&r.volts<=13.2f;
  r.state=r.volts>18.f?State::OverRange:State::Supply;
  return r;
}
}
