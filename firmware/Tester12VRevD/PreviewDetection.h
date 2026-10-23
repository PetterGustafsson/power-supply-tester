#pragma once
#include "Measurement.h"

namespace tester {
// Provisional LCD estimates only. CSV/calibration retain their unmodified
// eight-scan, 0.25 V peak-to-peak stability requirement.
class PreviewDetector {
  static constexpr unsigned kWindow=4;
  float samples[kWindow][kInputs]{};
  unsigned count=0,agreements=0,missed=0;
  bool established=false,windowReady=false;
  Result previous{},known{};
 public:
  void reset(){count=0;agreements=0;missed=0;established=false;windowReady=false;previous=Result{};known=Result{};}
  bool ready() const{return windowReady;}
  bool push(const float *sample,Result &out){
    for(int i=0;i<kInputs;i++){
      if(!std::isfinite(sample[i])){reset();return false;}
      samples[count][i]=sample[i];
    }
    if(++count<kWindow)return false;
    count=0;
    float center[kInputs],low[kInputs],high[kInputs];
    unsigned quiet[kInputs]{};
    for(int i=0;i<kInputs;i++){
      float sorted[kWindow];
      for(unsigned n=0;n<kWindow;n++){
        sorted[n]=samples[n][i];
        if(std::fabs(sorted[n])<=.35f)quiet[i]++;
      }
      for(unsigned n=1;n<kWindow;n++)for(unsigned j=n;j>0&&sorted[j]<sorted[j-1];j--){
        const float value=sorted[j];sorted[j]=sorted[j-1];sorted[j-1]=value;
      }
      low[i]=sorted[0];high[i]=sorted[kWindow-1];
      center[i]=(sorted[1]+sorted[2])*.5f;
    }
    Result candidate=classify(center,true);
    if(candidate.state==State::Ambiguous){
      // Sequential mux samples see bounded reference ripple at different
      // phases. Remove only that shared pole offset for provisional model
      // validation; the positive-minus-negative voltage is unchanged.
      float sp=0,sn=0;unsigned np=0,nn=0;bool quietInputs=true;
      uint16_t pos=0,neg=0;
      for(int i=0;i<kInputs;i++){
        if(center[i]>.35f){sp+=center[i];np++;pos|=1u<<i;}
        else if(center[i]<-.35f){sn+=center[i];nn++;neg|=1u<<i;}
        else if(std::fabs(center[i])>.20f)quietInputs=false;
      }
      if(np&&nn&&quietInputs){
        const float volts=sp/np-sn/nn,offset=(sp+sn)/(np+nn);
        if(std::fabs(offset)<=fmaxf(.75f,volts*.06f)){
          float aligned[kInputs];
          for(int i=0;i<kInputs;i++)aligned[i]=center[i]-(((pos|neg)&(1u<<i))?offset:0);
          const Result adjusted=classify(aligned,true);
          if(adjusted.positiveMask==pos&&adjusted.returnMask==neg)candidate=adjusted;
        }
      }
    }
    if(candidate.state==State::NoVoltage){reset();return false;}
    // Once identified, verify the same contacts are still energized instead
    // of repeatedly restarting identification because of reference ripple.
    // This requires fresh evidence in every accepted window, not a stale hold.
    if(established){
      bool present=true;float sp=0,sn=0;unsigned np=0,nn=0;
      const float span=fmaxf(1.5f,known.volts*.20f);
      for(int i=0;i<kInputs&&present;i++){
        const uint16_t bit=1u<<i;
        if(known.positiveMask&bit){
          present=low[i]>=.75f&&high[i]-low[i]<=span;sp+=center[i];np++;
        }else if(known.returnMask&bit){
          present=high[i]<=-.75f&&high[i]-low[i]<=span;sn+=center[i];nn++;
        }else present=std::fabs(center[i])<=.20f&&quiet[i]>=3&&low[i]>=-.75f&&high[i]<=.75f;
      }
      const float vp=np?sp/np:0,vn=nn?sn/nn:0,volts=vp-vn;
      present=present&&np&&nn&&volts>=9.f&&volts<=18.f&&
        std::fabs((sp+sn)/(np+nn))<=fmaxf(.75f,volts*.06f)&&
        std::fabs(volts-known.volts)<=fmaxf(.8f,known.volts*.10f);
      for(int i=0;i<kInputs&&present;i++){
        const uint16_t bit=1u<<i;
        if(known.positiveMask&bit)present=std::fabs(center[i]-vp)<=.5f;
        else if(known.returnMask&bit)present=std::fabs(center[i]-vn)<=.5f;
      }
      if(present){
        known.volts=known.volts*.8f+volts*.2f;
        known.nominal12=known.volts>=10.8f&&known.volts<=13.2f;
        out=known;previous=candidate;agreements=2;missed=0;windowReady=true;return true;
      }
    }
    bool acceptable=candidate.state==State::Supply&&candidate.volts>=9.f&&candidate.volts<=18.f;
    const float poleSpan=fmaxf(1.5f,candidate.volts*.20f);
    for(int i=0;i<kInputs&&acceptable;i++){
      const uint16_t bit=1u<<i;
      if(candidate.positiveMask&bit)
        acceptable=low[i]>=.75f&&high[i]-low[i]<=poleSpan;
      else if(candidate.returnMask&bit)
        acceptable=high[i]<=-.75f&&high[i]-low[i]<=poleSpan;
      else
        // One bounded spike on an otherwise quiet input must not postpone
        // recognition indefinitely. Sustained/intermediate inputs still fail.
        acceptable=quiet[i]>=3&&low[i]>=-.75f&&high[i]<=.75f;
    }
    if(!acceptable){
      agreements=0;windowReady=false;
      if(++missed>=8)established=false;
      return false;
    }
    const bool agrees=agreements&&candidate.positiveMask==previous.positiveMask&&
      candidate.returnMask==previous.returnMask&&
      std::fabs(candidate.volts-previous.volts)<=fmaxf(.4f,candidate.volts*.05f);
    agreements=agrees?2:1;previous=candidate;windowReady=agreements>=2;
    if(!ready())return false;
    known=candidate;established=true;missed=0;out=candidate;return true;
  }
};
}
