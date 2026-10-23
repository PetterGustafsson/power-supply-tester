// Render production graphics from explicit measurement fixtures; never opens USB.
#include "../../../firmware/Tester12VRevD/DisplayGraphics.h"
#include <cassert>
#include <fstream>
#include <limits>
#include <string>
#include <vector>
#include <cstdio>
static constexpr int count=240*240;
static uint16_t guarded[count+16];
static uint16_t *pixels=guarded+8;
static void guard(){for(int i=0;i<8;i++)assert(guarded[i]==0xa55a&&guarded[count+8+i]==0xa55a);}
static void output(const std::string &path){
  std::ofstream file(path,std::ios::binary);file<<"P6\n240 240\n255\n";
  for(int i=0;i<count;i++){
    const uint16_t v=tester_ui::Canvas::swap(pixels[i]);
    char rgb[3]={char(((v>>11)&31)*255/31),char(((v>>5)&63)*255/63),char((v&31)*255/31)};
    file.write(rgb,3);
  }
}
int main(int argc,char **argv){
  assert(argc==2);const std::string dir=argv[1];
  for(auto &v:guarded)v=0xa55a;
  tester_ui::Canvas canvas(pixels);canvas.put(0,0,0xf800);
  const auto bytes=reinterpret_cast<const unsigned char*>(pixels);assert(bytes[0]==0xf8&&bytes[1]==0);
  canvas.put(-1,-1,0xffff);canvas.blend(240,240,0xffff,255);guard();
  // The baked font is proportional and contains fractional edge coverage.
  using namespace tester_ui;
  assert(width("III",type::labelFont)<width("WWW",type::labelFont));
  assert(width("",type::labelFont)==0&&width(" ",type::labelFont)>0);
  assert(&glyph(type::labelFont,0)==&glyph(type::labelFont,'?'));
  const type::Font fonts[]={type::pinFont,type::labelFont,type::statusFont,type::valueFont};
  const size_t sizes[]={sizeof(type::pinCoverage),sizeof(type::labelCoverage),sizeof(type::statusCoverage),sizeof(type::valueCoverage)};
  bool antialiased=false;
  for(unsigned f=0;f<4;f++)for(unsigned c=32;c<=126;c++){
    const auto &g=glyph(fonts[f],c);
    assert(g.offset+(g.w*g.h+1)/2<=sizes[f]);
    for(unsigned y=0;y<g.h;y++)for(unsigned x=0;x<g.w;x++){
      const float v=Canvas::coverage(fonts[f],g,x,y);
      if(v>0&&v<255)antialiased=true;
    }
    // Rotated glyphs clipped at the screen boundary must preserve canaries.
    canvas.letter(fonts[f],g,c%2?0:239,c%3?0:239,c*.17f,0xffff);guard();
  }
  assert(antialiased);
  std::fill(pixels,pixels+count,0);
  canvas.arc("Circular lettering",100,-tau/4,type::labelFont,0xffff);
  int curvedPixels=0;
  for(int y=0;y<240;y++)for(int x=0;x<240;x++)if(pixels[y*240+x]){
    const float radius=std::hypot(x-120.f,y-120.f);
    assert(radius>95&&radius<114&&y<60);curvedPixels++;
  }
  assert(curvedPixels>200);guard();
  tester::Result r;r.state=tester::State::Supply;r.volts=12.03f;r.positiveMask=1;r.returnMask=2;r.unknownMask=0xffc;
  tester_ui::Options options;options.shared=true;
  assert(tester_ui::live(r,options));
  assert(width("111.11",type::valueFont)==width("888.88",type::valueFont));
  assert(kerning(type::labelFont,'A','V')<0);
  // Every precomputed path must run from the classified return to positive,
  // including reversed pairs. It is an illustration, not measured current.
  ElectronRoute routes[12];
  for(unsigned a=0;a<12;a++)for(unsigned b=0;b<12;b++)if(a!=b){
    assert(selectRoutes(1u<<b,1u<<a,routes)==1);
    assert(routes[0].from==a&&routes[0].to==b);
    const Point from=routePoint(routes[0],0),to=routePoint(routes[0],1);
    assert(std::hypot(from.x-pinPositions[a].x,from.y-pinPositions[a].y)<.1f);
    assert(std::hypot(to.x-pinPositions[b].x,to.y-pinPositions[b].y)<.1f);
  }
  assert(selectRoutes(1,0xffe,routes)==11);
  assert(selectRoutes(1,1,routes)==0&&selectRoutes(0x1000,2,routes)==0);
  for(unsigned i=0;i<14;i++){
    tester_ui::render(pixels,r,i*600,options);guard();
    char name[40];std::snprintf(name,sizeof(name),"/frame-%02u.ppm",i);output(dir+name);
  }
  assert(r.volts==12.03f&&r.positiveMask==1&&r.returnMask==2);
  tester_ui::render(pixels,r,900,options);std::vector<uint16_t> live(pixels,pixels+count);
  tester_ui::render(pixels,r,1400,options);assert(!std::equal(live.begin(),live.end(),pixels));
  // Only the protected inner stencil may change with animation time. Voltage,
  // typography and outer connector materials remain stationary.
  for(int y=0;y<240;y++)for(int x=0;x<240;x++)if(!Canvas::flowArea(x,y))assert(live[y*240+x]==pixels[y*240+x]);
  output(dir+"/pair-1-2.ppm");
  r.positiveMask=0x107;r.returnMask=0x8e0;r.unknownMask=0x618;
  tester_ui::render(pixels,r,900,options);guard();output(dir+"/multiple-pins.ppm");
  r.positiveMask=1;r.returnMask=0xffe;r.unknownMask=0;
  tester_ui::render(pixels,r,900,options);guard();output(dir+"/all-connected.ppm");
  for(unsigned i=0;i<14;i++){
    char name[48];
    r.returnMask=0x40;r.unknownMask=0xfbe;
    tester_ui::render(pixels,r,i*600,options);guard();
    std::snprintf(name,sizeof(name),"/pair-1-7-frame-%02u.ppm",i);output(dir+name);
    r.returnMask=0xffe;r.unknownMask=0;
    tester_ui::render(pixels,r,i*600,options);guard();
    std::snprintf(name,sizeof(name),"/all-frame-%02u.ppm",i);output(dir+name);
  }
  // Inactive/fault states must clear the previous pin colours, value and particles.
  r.state=tester::State::NoVoltage;r.volts=0;
  assert(!tester_ui::live(r,options));tester_ui::render(pixels,r,0,options);
  std::vector<uint16_t> idle(pixels,pixels+count);output(dir+"/no-voltage.ppm");
  tester_ui::render(pixels,r,1700,options);assert(std::equal(idle.begin(),idle.end(),pixels));
  r.state=tester::State::AdcFault;
  tester_ui::render(pixels,r,2000,options);std::vector<uint16_t> fault(pixels,pixels+count);output(dir+"/adc-fault.ppm");
  r.state=tester::State::Supply;r.volts=12;tester_ui::render(pixels,r,2500,options);
  r.state=tester::State::AdcFault;tester_ui::render(pixels,r,3000,options);
  assert(std::equal(fault.begin(),fault.end(),pixels));
  r.state=tester::State::OverRange;r.volts=19.25f;
  tester_ui::render(pixels,r,1200,options);guard();output(dir+"/over-range.ppm");
  r.state=tester::State::Ambiguous;options.unstable=true;
  tester_ui::render(pixels,r,1200,options);guard();output(dir+"/unstable.ppm");
  r.state=tester::State::CalibrationIncomplete;options.shared=false;options.calibrationReady=false;
  tester_ui::render(pixels,r,1200,options);output(dir+"/cal-required.ppm");
  r.state=tester::State::Supply;r.volts=12.03f;r.positiveMask=1;r.returnMask=2;options.shared=true;options.calibrationReady=true;
  options.capturing=true;assert(!tester_ui::live(r,options));tester_ui::render(pixels,r,1200,options);output(dir+"/capturing.ppm");
  options.capturing=false;options.stale=true;assert(!tester_ui::live(r,options));tester_ui::render(pixels,r,1200,options);output(dir+"/stale.ppm");
  options.stale=false;options.starting=true;assert(!tester_ui::live(r,options));tester_ui::render(pixels,r,1200,options);output(dir+"/starting.ppm");
  options.starting=false;r.volts=std::numeric_limits<float>::quiet_NaN();assert(!tester_ui::live(r,options));
  tester_ui::render(pixels,r,1200,options);guard();
  r.volts=12;r.returnMask=1;assert(!tester_ui::live(r,options));
  r.returnMask=0;assert(!tester_ui::live(r,options));
  r.returnMask=2;r.positiveMask=0x1000;assert(!tester_ui::live(r,options));
  // A copied static layer must exactly match fresh rendering, including transitions.
  std::vector<uint16_t> cache(count),cached(count),fresh(count),base(count);
  CachedRenderer renderer;options={};options.shared=true;
  r={};r.state=tester::State::Supply;r.volts=12.03f;r.positiveMask=1;r.returnMask=2;
  renderer.render(cached.data(),r,600,options,cache.data());const unsigned initialBuilds=renderer.rebuilds;
  r.volts=11.98f;renderer.render(cached.data(),r,1200,options,cache.data());
  assert(renderer.rebuilds==initialBuilds);render(fresh.data(),r,1200,options);assert(cached==fresh);
  for(unsigned step=0;step<12;step++){
    r.state=static_cast<tester::State>(step%6);r.positiveMask=step&1?1:4;r.returnMask=step&1?2:0x80;
    options.capturing=step==7;options.stale=step==8;options.starting=step==9;options.unstable=step==10;
    renderer.render(cached.data(),r,step*600,options,cache.data());render(fresh.data(),r,step*600,options);assert(cached==fresh);
  }
  renderer.render(cached.data(),r,7200,options,nullptr);render(fresh.data(),r,7200,options);assert(cached==fresh);
  puts("PASS: production renderer; all directed pin-pair paths, bounded routes, time-varying flashes confined to stencil, tabular digits, kerning, cache equality/fallback, antialiasing, bounds, state clearing and invalid masks.");
}
