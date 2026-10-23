#pragma once
#include "Measurement.h"
#include "ConnectorBackdrop.h"
#include "DisplayFont.h"
#include <cmath>
#include <cstdio>
#include <cstring>

// Pure renderer: real measurement states in, one RGB565 framebuffer out.
// Concentric instrument lettering: one reading, one brief status, pin polarity.
namespace tester_ui {
constexpr float tau=6.28318530718f;
constexpr uint16_t rgb(unsigned r,unsigned g,unsigned b) {
  return ((r>>3)<<11)|((g>>2)<<5)|(b>>3);
}
constexpr uint16_t warm=rgb(246,193,87),cold=rgb(91,205,221),silver=rgb(236,240,238);
constexpr uint16_t muted=rgb(154,166,173),red=rgb(225,139,126),green=rgb(139,174,153);
constexpr uint16_t outlineInk=rgb(17,21,22),alert=rgb(245,122,100);
inline const type::Glyph &glyph(const type::Font &font,unsigned char c){
  return font.glyphs[(c>=32&&c<=126?c:'?')-32];
}
inline float kerning(const type::Font &font,unsigned char a,unsigned char b){
  const unsigned key=(unsigned(a)<<8)|b;unsigned low=0,high=font.kernCount;
  while(low<high){
    const unsigned mid=(low+high)/2;const auto &pair=font.kerning[mid];
    const unsigned candidate=(unsigned(pair.a)<<8)|pair.b;
    if(candidate<key)low=mid+1;else high=mid;
  }
  return low<font.kernCount&&font.kerning[low].a==a&&font.kerning[low].b==b?font.kerning[low].adjustment/64.f:0;
}
inline float width(const char *s,const type::Font &font,float tracking=0){
  float result=0;unsigned char previous=0;
  for(const char *p=s;*p;p++){
    result+=glyph(font,*p).advance/64.f+tracking+kerning(font,previous,*p);previous=*p;
  }
  return *s?result-tracking:0;
}
class Canvas {
  uint16_t *frame;
 public:
  explicit Canvas(uint16_t *buffer):frame(buffer){}
  static uint16_t swap(uint16_t v){return uint16_t((v>>8)|(v<<8));}
  void put(int x,int y,uint16_t color){
    if(x<0||x>=240||y<0||y>=240)return;
    frame[y*240+x]=swap(color);
  }
  void blend(int x,int y,uint16_t color,unsigned alpha){
    if(x<0||x>=240||y<0||y>=240||!alpha)return;
    if(alpha>255)alpha=255;
    const uint16_t old=swap(frame[y*240+x]);const unsigned inv=255-alpha;
    const unsigned r=(((old>>11)&31)*inv+((color>>11)&31)*alpha)/255;
    const unsigned g=(((old>>5)&63)*inv+((color>>5)&63)*alpha)/255;
    const unsigned b=((old&31)*inv+(color&31)*alpha)/255;
    put(x,y,(r<<11)|(g<<5)|b);
  }
  static float coverage(const type::Font &font,const type::Glyph &g,float x,float y,const uint8_t *data=nullptr){
    if(!data)data=font.coverage;
    const int ix=int(std::floor(x)),iy=int(std::floor(y));const float dx=x-ix,dy=y-iy;
    auto at=[&](int px,int py)->float{
      if(px<0||py<0||px>=g.w||py>=g.h)return 0;
      const unsigned i=py*g.w+px;const uint8_t packed=data[g.offset+i/2];
      return float((i&1)?packed&15:packed>>4)*17;
    };
    return (at(ix,iy)*(1-dx)+at(ix+1,iy)*dx)*(1-dy)+
           (at(ix,iy+1)*(1-dx)+at(ix+1,iy+1)*dx)*dy;
  }
  void letter(const type::Font &font,const type::Glyph &g,float x,float y,float angle,uint16_t color){
    if(!g.w||!g.h)return;
    const float cs=std::cos(angle),sn=std::sin(angle);
    const float left=g.x*.5f-1,right=(g.x+g.w)*.5f+1;
    const float top=g.y*.5f-1,bottom=(g.y+g.h)*.5f+1;
    float x0=240,y0=240,x1=0,y1=0;
    for(int i=0;i<4;i++){
      const float u=(i&1)?right:left,v=(i&2)?bottom:top;
      const float px=x+cs*u-sn*v,py=y+sn*u+cs*v;
      x0=std::fmin(x0,px);x1=std::fmax(x1,px);y0=std::fmin(y0,py);y1=std::fmax(y1,py);
    }
    for(int py=int(std::fmax(0,std::floor(y0)));py<=int(std::fmin(239,std::ceil(y1)));py++)
      for(int px=int(std::fmax(0,std::floor(x0)));px<=int(std::fmin(239,std::ceil(x1)));px++){
        const float dx=px+.5f-x,dy=py+.5f-y;
        const float u=2*(cs*dx+sn*dy)-g.x-.5f,v=2*(-sn*dx+cs*dy)-g.y-.5f;
        const float ink=coverage(font,g,u,v);
        if(font.outline)blend(px,py,outlineInk,unsigned(coverage(font,g,u,v,font.outline)));
        blend(px,py,color,unsigned(ink));
      }
  }
  void text(const char *s,float x,float baseline,const type::Font &font,uint16_t color,float tracking=0){
    unsigned char previous=0;
    for(;*s;s++){const auto &g=glyph(font,*s);x+=kerning(font,previous,*s);letter(font,g,x,baseline,0,color);x+=g.advance/64.f+tracking;previous=*s;}
  }
  void arc(const char *s,float radius,float angle,const type::Font &font,uint16_t color,bool bottom=false,float tracking=.35f){
    if(radius<=0)return;
    float cursor=-width(s,font,tracking)*.5f;unsigned char previous=0;
    for(;*s;s++){
      const auto &g=glyph(font,*s);cursor+=kerning(font,previous,*s);const float advance=g.advance/64.f;
      const float a=angle+(bottom?-1:1)*(cursor+advance*.5f)/radius;
      const float rotation=a+(bottom?-tau/4:tau/4);
      const float x=120+radius*std::cos(a)-std::cos(rotation)*advance*.5f;
      const float y=120+radius*std::sin(a)-std::sin(rotation)*advance*.5f;
      letter(font,g,x,y,rotation,color);cursor+=advance+tracking;previous=*s;
    }
  }
  void ring(float cx,float cy,float radius,float thickness,uint16_t color,unsigned alpha=255){
    const int n=int(radius*tau*1.7f)+1;
    for(int i=0;i<n;i++){
      const float a=tau*i/n;
      for(float r=radius-thickness*.5f;r<=radius+thickness*.5f;r+=.55f)
        blend(int(std::lround(cx+r*std::cos(a))),int(std::lround(cy+r*std::sin(a))),color,alpha);
    }
  }
  void centered(const char *s,float baseline,const type::Font &font,uint16_t color,float tracking=0){
    text(s,120-width(s,font,tracking)*.5f,baseline,font,color,tracking);
  }
  void disc(float cx,float cy,float radius,uint16_t color){
    for(int y=int(cy-radius-1);y<=int(cy+radius+1);y++)for(int x=int(cx-radius-1);x<=int(cx+radius+1);x++){
      const float d=std::sqrt((x+.5f-cx)*(x+.5f-cx)+(y+.5f-cy)*(y+.5f-cy));
      if(d<radius+.5f)blend(x,y,color,unsigned(255*std::fmin(1.f,radius+.5f-d)));
    }
  }
};
struct Options {bool shared=false,capturing=false,starting=false,stale=false,unstable=false,calibrationReady=true;};
inline bool live(const tester::Result &r,const Options &o){
  return !o.capturing&&!o.starting&&!o.stale&&
    (r.state==tester::State::Supply||r.state==tester::State::OverRange)&&
    std::isfinite(r.volts)&&r.volts>0&&r.positiveMask&&r.returnMask&&
    !(r.positiveMask&r.returnMask)&&!((r.positiveMask|r.returnMask)&~tester::kAllPins);
}
inline void renderBase(uint16_t *buffer,const tester::Result &r,Options o={}){
  // Preserve the source metal, knurling, recesses and plastic without washes.
  std::memcpy(buffer,connectorBackdrop,sizeof(connectorBackdrop));Canvas c(buffer);
  const bool powered=live(r,o);const uint16_t hot=r.state==tester::State::OverRange?red:warm;
  for(unsigned i=0;i<12;i++){
    const Point p=pinPositions[i];const bool pos=powered&&(r.positiveMask&(1u<<i));
    const bool neg=powered&&(r.returnMask&(1u<<i));const uint16_t color=pos?hot:neg?cold:muted;
    if(pos||neg){
      c.ring(p.x,p.y,7.7f,1.5f,color,30);c.ring(p.x,p.y,6.5f,1.f,color,225);
      const char *sign=pos?"+":"-";
      c.text(sign,p.x-width(sign,type::pinFont)*.5f,p.y+3.5f,type::pinFont,color);
    }
    char number[4];std::snprintf(number,sizeof(number),"%u",i+1);
    if(i<9){
      const float dx=p.x-120,dy=p.y-120,angle=std::atan2(dy,dx);
      const bool bottom=dy>0;
      // The lower baseline moves outward by the cap height, keeping every
      // number's ink on the same circular track and readable from outside.
      c.arc(number,std::sqrt(dx*dx+dy*dy)+(bottom?22:13),angle,type::pinFont,color,bottom,0);
    }else c.text(number,p.x-width(number,type::pinFont)*.5f,p.y-8,type::pinFont,color);
  }
  const char *headline=nullptr;uint16_t ink=silver;
  if(o.starting)headline="STARTING";
  else if(o.capturing){headline="READING";ink=warm;}
  else if(o.stale){headline="NO DATA";ink=warm;}
  else if(powered){
    if(r.state==tester::State::OverRange)
      c.arc("OVER RANGE",96,tau/4,type::labelFont,alert,true,.8f);
  }
  else if(r.state==tester::State::NoVoltage)headline="NO VOLTAGE";
  else if(r.state==tester::State::AdcFault){headline="SENSOR FAULT";ink=alert;}
  else if(r.state==tester::State::CalibrationIncomplete){headline="NOT READY";ink=warm;}
  else{headline=o.unstable?"HOLD STEADY":"CHECK LEADS";ink=warm;}
  if(headline)c.arc(headline,82,-tau/4,type::statusFont,ink,false,.45f);
}
inline void renderDynamic(uint16_t *buffer,const tester::Result &r,uint32_t now,Options o={}){
  (void)now;if(!live(r,o))return;
  Canvas c(buffer);char value[24];std::snprintf(value,sizeof(value),"%.2f",r.volts);
  // A shared circular baseline centres the whole reading. The smaller unit
  // follows the same tangent; tabular digit advances keep updates settled.
  constexpr float radius=77,tracking=.05f,gap=5;
  const float valueWidth=width(value,type::valueFont,tracking),unitWidth=width("V",type::labelFont);
  c.arc(value,radius,-tau/4-(unitWidth+gap)/(2*radius),type::valueFont,
    r.state==tester::State::OverRange?alert:silver,false,tracking);
  c.arc("V",radius,-tau/4+(valueWidth+gap)/(2*radius),type::labelFont,silver,false,0);
}
inline void render(uint16_t *buffer,const tester::Result &r,uint32_t now,Options o={}){
  renderBase(buffer,r,o);renderDynamic(buffer,r,now,o);
}
class CachedRenderer {
  uint16_t *lastCache=nullptr;uint16_t positive=0,negative=0,flags=0;tester::State state=tester::State::AdcFault;
 public:
  unsigned rebuilds=0;
  void render(uint16_t *buffer,const tester::Result &r,uint32_t now,Options o,uint16_t *cache){
    if(!cache||cache==buffer){tester_ui::render(buffer,r,now,o);return;}
    const uint16_t key=(o.shared?1:0)|(o.capturing?2:0)|(o.starting?4:0)|(o.stale?8:0)|
      (o.unstable?16:0)|(o.calibrationReady?32:0)|(live(r,o)?64:0);
    if(lastCache!=cache||positive!=r.positiveMask||negative!=r.returnMask||state!=r.state||flags!=key){
      renderBase(cache,r,o);lastCache=cache;positive=r.positiveMask;negative=r.returnMask;
      state=r.state;flags=key;rebuilds++;
    }
    std::memcpy(buffer,cache,sizeof(connectorBackdrop));renderDynamic(buffer,r,now,o);
  }
};
} // namespace tester_ui
