#include "../../../firmware/Tester12V/Measurement.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>
using namespace tester;
int main(int argc,char **argv) {
  assert(argc==2);std::ifstream f(argv[1]);assert(f.good());std::string line;getline(f,line);int cases=0;
  while(getline(f,line)) {
    std::vector<float> cols;std::stringstream s(line);std::string cell;
    while(getline(s,cell,','))cols.push_back(std::stof(cell));
    assert(cols.size()==16);float v[12];for(int i=0;i<12;i++)v[i]=cols[4+i]*kNominalGain;
    auto r=classify(v,true);float applied=cols[2];
    if(applied==0)assert(r.state==State::NoPair);
    else if(applied<=18) {assert(r.state==State::Pair);assert(r.positive==cols[0]-1);assert(r.negative==cols[1]-1);assert(r.nominal12==(applied==12));}
    else assert(r.state==State::OverRange);
    cases++;
  }
  float v[12]={};
  assert(classify(v,false).state==State::AdcFault);
  v[0]=std::numeric_limits<float>::quiet_NaN();assert(classify(v,true).state==State::AdcFault);v[0]=0;
  v[0]=6;v[1]=-6;v[2]=4;assert(classify(v,true).state==State::Ambiguous);
  v[2]=0;v[1]=0;assert(classify(v,true).state==State::Ambiguous);
  v[1]=-6;assert(classify(v,true).nominal12);
  // Channel ordering and nominal window edge checks, independent of circuit model.
  for(int hi=0;hi<12;hi++)for(int lo=0;lo<12;lo++)if(hi!=lo) {
    for(auto &x:v)x=0;
    v[hi]=6;v[lo]=-6;auto r=classify(v,true);assert(r.positive==hi&&r.negative==lo&&r.nominal12);
  }
  for(auto &x:v)x=0;v[0]=5;v[1]=-5;assert(!classify(v,true).nominal12);
  assert(cases==1188);
  puts("PASS: 1188 exported-netlist cases, 132 independent pin permutations, ADC fault/NaN, multi-rail, unbalanced source and voltage-window checks.");
}
