#pragma once
#include <cmath>
#include <cstdint>

// A single NVS blob keeps each low point tied to the calibration pass that made it.
struct CalibrationBatch {
  uint32_t format=0x43414c32; // CAL2
  uint32_t id=0;
  uint16_t lowMask=0, doneMask=0;
  float low[12]={};
  bool valid() const {
    if(format!=0x43414c32 || (lowMask&0xf000) || (doneMask&~lowMask))return false;
    for(int i=0;i<12;i++)if((lowMask&(1u<<i)) && (!std::isfinite(low[i]) || std::fabs(low[i])>.01f))return false;
    return true;
  }
};
