#pragma once
#include <cmath>
#include <cstdint>

namespace tester {
constexpr int kInputs = 12;
constexpr float kNominalGain = 37.3f;
enum class State { NoPair, Pair, Ambiguous, OverRange, AdcFault, CalibrationIncomplete };
struct Result { State state; int positive, negative; float volts; bool nominal12; };

// Values are corrected input-referred voltages. Only differences are meaningful:
// this floating instrument cannot identify earth, chassis ground, or continuity.
inline Result classify(const float *v, bool acquisitionOK) {
  Result r{State::AdcFault, -1, -1, 0, false};
  if (!acquisitionOK) return r;
  float sorted[kInputs];
  int lo=0, hi=0;
  for (int i=0;i<kInputs;i++) {
    if (!std::isfinite(v[i])) return r;
    sorted[i]=v[i];
    if (v[i]<v[lo]) lo=i;
    if (v[i]>v[hi]) hi=i;
  }
  for (int i=1;i<kInputs;i++) {
    float x=sorted[i]; int j=i-1;
    while (j>=0 && sorted[j]>x) { sorted[j+1]=sorted[j]; --j; }
    sorted[j+1]=x;
  }
  const float middle=(sorted[5]+sorted[6])*0.5f;
  r.volts=v[hi]-v[lo];
  if (r.volts<0.5f) { r.state=State::NoPair; return r; }
  r.positive=hi; r.negative=lo;
  if (r.volts>18.0f) { r.state=State::OverRange; return r; }
  // A single floating source should produce two opposite deviations, with ten
  // otherwise quiet pins. Reject additional rails and strong imbalance.
  float quietSpread=0;
  for (int i=0;i<kInputs;i++) if (i!=hi && i!=lo)
    quietSpread=fmaxf(quietSpread,fabsf(v[i]-middle));
  if (quietSpread>0.35f || v[hi]-middle<0.18f || middle-v[lo]<0.18f ||
      fabsf(v[hi]+v[lo]-2*middle)>fmaxf(0.6f,r.volts*0.12f)) {
    r.state=State::Ambiguous; return r;
  }
  r.state=State::Pair;
  r.nominal12=r.volts>=10.8f && r.volts<=13.2f;
  return r;
}
}
