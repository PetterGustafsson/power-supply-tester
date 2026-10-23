#pragma once
#include <Arduino.h>
#include <esp_partition.h>
#include <esp_heap_caps.h>
#include <miniz.h>
#include <cmath>
#include <cstdio>
#include <cstring>
#include "LCD_1in28.h"
#include "Measurement.h"
#include "LiveMark.h"

// The flash asset holds only the connector, metal and optical travel. Every
// electrical mark below is drawn from the latest accepted ADC classification.
namespace live_optics {
constexpr int kWidth=240,kBytes=kWidth*kWidth*2,kFrameUs=20000,kMaxCompressed=50000;
constexpr uint16_t rgb(unsigned r,unsigned g,unsigned b){return ((r>>3)<<11)|((g>>2)<<5)|(b>>3);}
constexpr uint16_t ice=rgb(212,248,255),cyan=rgb(79,205,255),gold=rgb(255,201,87);
constexpr uint16_t emerald=rgb(142,255,172),red=rgb(249,83,66),violet=rgb(194,128,255);
struct __attribute__((packed)) AssetHeader {
  char magic[8];uint32_t version,width,fps,frames,payloadOffset,payloadBytes,payloadCrc,reserved;
};
struct __attribute__((packed)) FrameMeta {
  uint32_t offset,length;uint8_t x0,y0,x1,y1,flags;
};
static_assert(sizeof(AssetHeader)==40,"Live asset header");
static_assert(sizeof(FrameMeta)==13,"Live frame metadata");

struct Pt{float x,y;};
constexpr Pt pin[12]={{106.6f,83.6f},{86.4f,104.5f},{81.8f,126.8f},
  {95.0f,149.6f},{120.0f,158.8f},{145.0f,149.6f},{158.2f,126.8f},
  {153.6f,104.5f},{133.4f,83.6f},{120.0f,100.5f},{106.6f,127.8f},{133.4f,127.8f}};

class Canvas {
  uint16_t *data;
  static uint16_t swap(uint16_t value){return (value>>8)|(value<<8);}
 public:
  explicit Canvas(uint16_t *buffer):data(buffer){}
  void blend(int x,int y,uint16_t color,unsigned alpha,bool additive=false){
    if(x<0||y<0||x>=kWidth||y>=kWidth||!alpha)return;
    if(alpha>255)alpha=255;
    const unsigned index=y*kWidth+x,old=swap(data[index]),inv=255-alpha;
    unsigned r=additive?((old>>11)&31)+(((color>>11)&31)*alpha/255):((((old>>11)&31)*inv+((color>>11)&31)*alpha)/255);
    unsigned g=additive?((old>>5)&63)+(((color>>5)&63)*alpha/255):((((old>>5)&63)*inv+((color>>5)&63)*alpha)/255);
    unsigned b=additive?(old&31)+((color&31)*alpha/255):(((old&31)*inv+(color&31)*alpha)/255);
    data[index]=swap(((r>31?31:r)<<11)|((g>63?63:g)<<5)|(b>31?31:b));
  }
  void dot(float fx,float fy,float radius,uint16_t color,unsigned alpha,bool additive=true){
    const int left=int(fx-radius-1),right=int(fx+radius+1),top=int(fy-radius-1),bottom=int(fy+radius+1);
    const float edge=(radius+.5f)*(radius+.5f),soft=2*radius+1.f;
    for(int y=top;y<=bottom;y++)for(int x=left;x<=right;x++){
      const float dx=x+.5f-fx,dy=y+.5f-fy,inside=edge-dx*dx-dy*dy;
      if(inside>0)blend(x,y,color,unsigned(alpha*std::fmin(1.f,inside/soft)),additive);
    }
  }
  void line(Pt a,Pt b,uint16_t color,unsigned alpha,int width=1,bool additive=true){
    const unsigned steps=unsigned(std::ceil(std::fmax(std::fabs(a.x-b.x),std::fabs(a.y-b.y))))+1;
    const float dx=b.x-a.x,dy=b.y-a.y,length=std::sqrt(dx*dx+dy*dy);
    const float nx=length>.01f?-dy/length:0,ny=length>.01f?dx/length:0;
    for(unsigned i=0;i<=steps;i++){
      const float x=a.x+(b.x-a.x)*i/steps,y=a.y+(b.y-a.y)*i/steps;
      if(width<=1)blend(int(std::lround(x)),int(std::lround(y)),color,alpha,additive);
      else for(int offset=-width/2;offset<=(width-1)/2;offset++){
        const unsigned edge=(abs(offset)==width/2)?alpha*3/4:alpha;
        blend(int(std::lround(x+nx*offset)),int(std::lround(y+ny*offset)),color,edge,additive);
      }
    }
  }
  void ring(Pt p,float radius,uint16_t color,unsigned alpha){
    for(int i=0;i<96;i++){
      const float a=6.2831853f*i/96,b=6.2831853f*(i+1)/96;
      line({p.x+radius*std::cos(a),p.y+radius*std::sin(a)},
           {p.x+radius*std::cos(b),p.y+radius*std::sin(b)},color,alpha);
    }
  }
};

inline uint16_t mix(uint16_t a,uint16_t b,unsigned u){
  if(u>255)u=255;const unsigned v=255-u;
  return (((((a>>11)&31)*v+((b>>11)&31)*u)/255)<<11)|
         (((((a>>5)&63)*v+((b>>5)&63)*u)/255)<<5)|
         (((a&31)*v+(b&31)*u)/255);
}
inline uint32_t hash(uint32_t n){n^=n<<13;n^=n>>17;n^=n<<5;return n;}

inline void voltage(Canvas &canvas,float volts,unsigned opacity,bool overRange){
  if(!std::isfinite(volts)||volts<0||volts>=100.f)return;
  char reading[12];std::snprintf(reading,sizeof(reading),"%.2f V",volts);
  static constexpr float segment[7][4]={{-2,-3.8f,2,-3.8f},{2.4f,-3.3f,2.4f,-.5f},
    {2.4f,.5f,2.4f,3.3f},{-2,3.8f,2,3.8f},{-2.4f,.5f,-2.4f,3.3f},
    {-2.4f,-3.3f,-2.4f,-.5f},{-2,0,2,0}};
  const char *digits[10]={"abcdef","bc","abged","abgcd","fgbc","afgcd",
    "afgcde","abc","abcdefg","abcdfg"};
  // The hand cut seven-segment readout follows the upper enamel pocket.
  float total=0;const int length=std::strlen(reading);
  for(int i=0;i<length;i++)total+=(reading[i]=='.'?2.7f:reading[i]==' '?3.4f:reading[i]=='V'?6.6f:6.7f)*3.f;
  total+=(length-1)*2.55f;float cursor=-total*.5f;
  const uint16_t core=overRange?rgb(255,200,170):rgb(189,255,205);
  const uint16_t glow=overRange?red:emerald;
  for(int i=0;i<length;i++){
    const char c=reading[i];const float width=(c=='.'?2.7f:c==' '?3.4f:c=='V'?6.6f:6.7f)*3.f;
    const float angle=-1.5707963f+(cursor+width*.5f)/83.f;
    const Pt center={120+83*std::cos(angle),120+83*std::sin(angle)};
    const Pt tangent={-std::sin(angle),std::cos(angle)};
    const Pt inward={-std::cos(angle),-std::sin(angle)};
    auto point=[&](float x,float y)->Pt{return {center.x+3*(x*tangent.x+y*inward.x),
                                                  center.y+3*(x*tangent.y+y*inward.y)};};
    auto stroke=[&](Pt a,Pt b){
      canvas.line(a,b,glow,opacity/7,8);
      canvas.line(a,b,glow,opacity/3,5);
      canvas.line(a,b,core,opacity,3);
    };
    if(c>='0'&&c<='9'){
      const char *used=digits[c-'0'];
      // Six uses the lower left segment as well as the middle bar.
      if(c=='6')used="afgcde";
      for(const char *p=used;*p;p++){
        const float *s=segment[*p-'a'];stroke(point(s[0],s[1]),point(s[2],s[3]));
      }
    }else if(c=='.')canvas.dot(point(0,3.4f).x,point(0,3.4f).y,1.6f,core,opacity);
    else if(c=='V'){
      stroke(point(-2.3f,-3.6f),point(0,3.7f));
      stroke(point(0,3.7f),point(2.3f,-3.6f));
    }
    cursor+=width+2.55f;
  }
}

inline void logo(Canvas &canvas,bool recognized,unsigned opacity){
  const int x0=103,y0=193;
  for(int y=0;y<21;y++)for(int x=0;x<34;x++){
    const unsigned i=y*34+x,a=unsigned(live_mark::alpha[i])*opacity/255;
    if(!a)continue;
    const uint16_t ink=recognized?live_mark::color[i]:mix(live_mark::color[i],rgb(148,145,145),190);
    canvas.blend(x0+x,y0+y,ink,recognized?a:a*145/255);
  }
  if(!recognized){
    const uint16_t cross=rgb(200,165,163);
    canvas.line({107,196},{133,210},cross,opacity*125/255,1,false);
    canvas.line({107,210},{133,196},cross,opacity*125/255,1,false);
  }
}

inline void polarity(Canvas &c,const tester::Result &r,unsigned opacity){
  for(unsigned i=0;i<12;i++){
    const bool positive=r.positiveMask&(1u<<i),negative=r.returnMask&(1u<<i);
    if(!positive&&!negative)continue;
    const uint16_t color=positive?red:cyan;const Pt p=pin[i];
    c.ring(p,8.5f,color,opacity*135/255);
    c.ring(p,9.5f,color,opacity*58/255);
    c.line({p.x-2.4f,p.y},{p.x+2.4f,p.y},rgb(13,22,25),opacity,2,false);
    if(positive)c.line({p.x,p.y-2.4f},{p.x,p.y+2.4f},rgb(13,22,25),opacity,2,false);
  }
}

inline void discharge(Canvas &c,const tester::Result &r,uint32_t now,unsigned opacity){
  unsigned positives[12],negatives[12],np=0,nn=0;
  for(unsigned i=0;i<12;i++){
    if(r.positiveMask&(1u<<i))positives[np++]=i;
    if(r.returnMask&(1u<<i))negatives[nn++]=i;
  }
  if(!np||!nn)return;
  const unsigned pairs=np>nn?np:nn;
  const float phase=(now%1000)/1000.f;
  for(unsigned route=0;route<pairs;route++){
    const Pt start=pin[negatives[route%nn]],end=pin[positives[route%np]];
    const float dx=end.x-start.x,dy=end.y-start.y,length=std::hypot(dx,dy);
    if(length<2)continue;
    const float nx=-dy/length,ny=dx/length;
    const float arch=std::fmin(13.f,length*.17f)*((nx*(start.x+end.x-240)+ny*(start.y+end.y-240))>=0?1.f:-1.f);
    auto at=[&](float u,float side=0)->Pt{
      const float ripple=std::sin(3.1415927f*u)*(arch+3*std::sin(6.2831853f*(u*1.4f-phase))+side);
      return {start.x+dx*u+nx*ripple,start.y+dy*u+ny*ripple};
    };
    for(unsigned j=0;j<32;j++){
      const float u=j/32.f,v=(j+1)/32.f;const uint16_t color=mix(cyan,gold,unsigned(u*255));
      c.line(at(u),at(v),color,opacity*65/255,4);
      c.line(at(u),at(v),color,opacity*160/255,2);
    }
    const float head=phase*phase*(3-2*phase),tail=std::fmax(0.f,head-.72f);
    for(unsigned strand=0;strand<3;strand++){
      const float side=strand==0?0:strand==1?5.2f:-5.2f;
      Pt prior=at(tail,side);
      for(unsigned j=1;j<=30;j++){
        const float u=tail+(head-tail)*j/30.f;const Pt p=at(u,side);
        const uint16_t color=mix(cyan,gold,unsigned(u*255));
        const unsigned alpha=opacity*(strand?135:220)/255;
        c.line(prior,p,color,alpha/3,strand?5:8);
        c.line(prior,p,color,alpha,strand?2:3);
        if(j>22&&strand==0)c.line(prior,p,ice,alpha/2,1);
        prior=p;
      }
    }
    const Pt tip=at(head);const uint16_t hot=head>.4f?gold:ice;
    c.dot(tip.x,tip.y,8,hot,opacity/5);c.dot(tip.x,tip.y,2,ice,opacity);
    c.line({tip.x-13*nx,tip.y-13*ny},{tip.x+10*nx,tip.y+10*ny},hot,opacity*185/255);
    c.line({tip.x-8*dx/length,tip.y-8*dy/length},
           {tip.x+7*dx/length,tip.y+7*dy/length},hot,opacity*135/255);
    for(unsigned i=0;i<11;i++){
      const uint32_t seed=hash(i*113u+route*97u+now/80);
      const float u=head-(i+1)*.045f;if(u<=0)continue;
      const float side=(i&1?1.f:-1.f)*(8+seed%11);const Pt p=at(u,side);
      const unsigned a=opacity*(80+(seed>>8)%140)/255;
      c.line({p.x-2,p.y},{p.x+3,p.y},u>.35f?gold:ice,a);
      c.line({p.x,p.y-2},{p.x,p.y+3},u>.35f?gold:ice,a);
    }
    if(phase>.68f){
      const float arrival=(phase-.68f)/.32f;const unsigned a=opacity*unsigned(arrival*220)/255;
      c.dot(end.x,end.y,12,gold,a/4);
      for(int i=-2;i<=2;i++){
        const Pt p={end.x+dx/length*(20+abs(i)*5)+nx*i*7,
                    end.y+dy/length*(20+abs(i)*5)+ny*i*7};
        c.line(end,p,gold,a/(abs(i)+1),1);
      }
    }
    // Pair 1/2 gets the theatrical white spectral helix, while the static
    // red mark remains anchored at six o'clock.
    if((r.positiveMask|r.returnMask)==3){
      for(int strand=0;strand<2;strand++){
        Pt before{};
        for(int j=0;j<=40;j++){
          const float u=j/40.f,wave=std::sin(6.2831853f*(1.28f*u+phase));
          const float offset=(strand? -1.f:1.f)*7.5f*std::cos(6.2831853f*(1.28f*u+phase))*std::sin(3.1415927f*u);
          const Pt p={start.x+dx*u+nx*offset,start.y+dy*u+ny*offset};
          if(j){
            const uint16_t spectral=(j%10<3)?violet:(j%10<6)?rgb(139,255,185):ice;
            const unsigned a=opacity*(wave*(strand?-1:1)>0?225:115)/255;
            c.line(before,p,spectral,a/2,6);c.line(before,p,ice,a,2);
          }
          before=p;
        }
      }
    }else if((now/95+route)%8<2){
      // Fleeting white blue fork for the unrecognized powered pair.
      Pt before=start;
      for(unsigned j=1;j<=7;j++){
        const float u=j/7.f;const uint32_t seed=hash(j*71u+now/90+route*111u);
        const float side=j==7?0:float(int(seed%17)-8);
        const Pt p={start.x+dx*u+nx*side,start.y+dy*u+ny*side};
        c.line(before,p,cyan,opacity/3,8);c.line(before,p,ice,opacity,2);before=p;
      }
    }
  }
}

enum Mode:uint8_t{IDLE,INSERT,POWERED,WITHDRAW,RECOGNIZED};
class Player {
  const esp_partition_t *partition=nullptr;AssetHeader header{};
  uint16_t *base=nullptr,*screen=nullptr,*voltageLayer=nullptr;uint8_t *compressed=nullptr,*delta=nullptr;
  struct VoltagePixel{uint8_t x,y;uint16_t color;};
  VoltagePixel *voltagePixels=nullptr;uint16_t voltagePixelCount=0;
  int voltageKey=-1;bool voltageAlert=false;
  QueueHandle_t requests=nullptr,results=nullptr;
  struct Request{uint16_t index;};
  struct Response{FrameMeta meta;uint16_t index;uint8_t error;uint32_t decodeUs;};
  Mode mode=IDLE;bool separate=false;uint16_t pending=0;uint32_t nextUs=0,reportAt=0,frames=0,lastFrames=0;
  uint32_t insertStartedAt=0;
  uint64_t decodeTime=0,overlayTime=0,transferTime=0;
  uint32_t benchPair[2]={0,0},benchDischarge[2]={0,0},benchVoltage[2]={0,0};
  static uint16_t first(Mode m){return m==IDLE?0:m==INSERT?140:m==POWERED?161:m==WITHDRAW?211:261;}
  static uint16_t end(Mode m){return m==IDLE?140:m==INSERT?161:m==POWERED?211:m==WITHDRAW?261:311;}
  static const char *name(Mode m){return m==IDLE?"IDLE":m==INSERT?"INSERT":
    m==POWERED?"POWERED":m==WITHDRAW?"WITHDRAW":"RECOGNIZED";}
  bool read(uint32_t offset,void *out,size_t length){
    return offset<=partition->size&&length<=partition->size-offset&&
      esp_partition_read(partition,offset,out,length)==ESP_OK;
  }
  static void workerEntry(void *arg){static_cast<Player*>(arg)->worker();}
  void worker(){
    Request req;
    for(;;){
      xQueueReceive(requests,&req,portMAX_DELAY);Response response{};response.index=req.index;
      if(!read(sizeof(AssetHeader)+req.index*sizeof(FrameMeta),&response.meta,sizeof(FrameMeta)))response.error=1;
      else if(!response.meta.length||response.meta.length>kMaxCompressed||
              response.meta.offset>header.payloadBytes||
              response.meta.length>header.payloadBytes-response.meta.offset||
              response.meta.x0>response.meta.x1||response.meta.x1>240||
              response.meta.y0>response.meta.y1||response.meta.y1>240)response.error=2;
      else{
        const uint32_t began=micros();
        if(!read(header.payloadOffset+response.meta.offset,compressed,response.meta.length))response.error=3;
        else if(tinfl_decompress_mem_to_mem(delta,kBytes,compressed,response.meta.length,
                   TINFL_FLAG_PARSE_ZLIB_HEADER)!=kBytes)response.error=4;
        response.decodeUs=micros()-began;
      }
      xQueueSend(results,&response,portMAX_DELAY);
    }
  }
  bool enqueue(uint16_t index){const Request request{index};return xQueueSend(requests,&request,0)==pdTRUE;}
  bool take(Response &response){
    if(xQueueReceive(results,&response,pdMS_TO_TICKS(1000))!=pdTRUE){Serial.println("DISPLAY_ERROR: decode timeout");return false;}
    if(response.error){Serial.printf("DISPLAY_ERROR: frame=%u code=%u\n",response.index,response.error);return false;}
    return true;
  }
  void apply(const Response &ready){
    uint8_t *bytes=reinterpret_cast<uint8_t*>(separate?base:screen);
    if(ready.meta.flags&1)std::memcpy(bytes,delta,kBytes);
    else for(int i=0;i<kBytes;i++)bytes[i]^=delta[i];
    decodeTime+=ready.decodeUs;
  }
  void drawVoltage(Canvas &canvas,float volts,unsigned opacity,bool overRange){
    if(!voltageLayer||!std::isfinite(volts))return;
    const int key=int(std::lround(volts*100.f));
    if(key!=voltageKey||overRange!=voltageAlert){
      std::memset(voltageLayer,0,kBytes);
      Canvas layer(voltageLayer);
      voltage(layer,key/100.f,255,overRange);
      voltagePixelCount=0;
      for(int y=8;y<88;y++)for(int x=32;x<208;x++){
        const uint16_t stored=voltageLayer[y*kWidth+x];
        if(stored)voltagePixels[voltagePixelCount++]={uint8_t(x),uint8_t(y),
          uint16_t((stored>>8)|(stored<<8))};
      }
      voltageKey=key;voltageAlert=overRange;
    }
    for(uint16_t i=0;i<voltagePixelCount;i++){
      const VoltagePixel &pixel=voltagePixels[i];
      canvas.blend(pixel.x,pixel.y,pixel.color,opacity,true);
    }
  }
  void overlay(const tester::Result &r,uint16_t index){
    const bool live=(r.state==tester::State::Supply||r.state==tester::State::OverRange)&&
      r.positiveMask&&r.returnMask&&std::isfinite(r.volts);
    unsigned opacity=0;
    if(live&&(mode==POWERED||mode==RECOGNIZED))opacity=255;
    else if(live&&mode==INSERT&&index>=155){
      const unsigned source=150+((index-140)*49+10)/20;
      opacity=(source-186)*255/13;
    }
    if(!opacity)return;
    Canvas canvas(screen);
    if(mode==RECOGNIZED){
      // The full source artwork already contains the pair, current and mark.
      // Only the numerals come from the actual ADC reading.
      drawVoltage(canvas,r.volts,opacity,r.state==tester::State::OverRange);
      return;
    }
    const bool accepted=(r.positiveMask|r.returnMask)==3;
    polarity(canvas,r,opacity);
    discharge(canvas,r,millis(),opacity);
    drawVoltage(canvas,r.volts,opacity,r.state==tester::State::OverRange);
    logo(canvas,accepted,opacity);
  }
  void show(const Response &ready,const tester::Result &r){
    const uint32_t overlayStart=micros();
    if(separate)std::memcpy(screen,base,kBytes);
    overlay(r,ready.index);
    overlayTime+=micros()-overlayStart;
    const uint32_t began=micros();
    if(!separate&&!(ready.meta.flags&1)&&ready.meta.x1>ready.meta.x0&&ready.meta.y1>ready.meta.y0)
      LCD_1IN28_DisplayWindows(ready.meta.x0,ready.meta.y0,ready.meta.x1,ready.meta.y1,screen);
    else if(separate||(ready.meta.flags&1))LCD_1IN28_Display(screen);
    transferTime+=micros()-began;frames++;
  }
  bool select(Mode selected){
    Response discard;if(!take(discard))return false;
    mode=selected;separate=false;pending=first(mode);
    if(mode==INSERT)insertStartedAt=millis();
    if(!enqueue(pending))return false;
    nextUs=micros();
    Serial.printf("DISPLAY_MODE: %s LIVE\n",name(mode));
    return true;
  }
 public:
  void benchmarkOverlay(){
    // RAM-only fixture: verifies the expensive live layers without sending a
    // simulated reading to the LCD or changing a sensor/calibration value.
    const Mode saved=mode;mode=POWERED;
    std::memcpy(base,screen,kBytes);
    tester::Result fixture;fixture.state=tester::State::Supply;fixture.volts=12.03f;
    for(unsigned pair=0;pair<2;pair++){
      fixture.positiveMask=1u<<(pair?6:1);fixture.returnMask=1u<<(pair?2:0);
      uint32_t total=0;
      for(unsigned i=0;i<4;i++){
        std::memcpy(screen,base,kBytes);const uint32_t began=micros();
        overlay(fixture,200);total+=micros()-began;
      }
      benchPair[pair]=total/4;
      Serial.printf("DISPLAY_BENCH pair=%s overlay_us=%lu\n",pair?"other":"allied",
        (unsigned long)benchPair[pair]);
      std::memcpy(screen,base,kBytes);Canvas measure(screen);
      const uint32_t began=micros();
      polarity(measure,fixture,255);const uint32_t afterPolarity=micros();
      discharge(measure,fixture,millis(),255);const uint32_t afterDischarge=micros();
      drawVoltage(measure,fixture.volts,255,false);const uint32_t afterVoltage=micros();
      logo(measure,!pair,255);const uint32_t afterLogo=micros();
      benchDischarge[pair]=afterDischarge-afterPolarity;
      benchVoltage[pair]=afterVoltage-afterDischarge;
      Serial.printf("DISPLAY_BENCH_PART pair=%s polarity_us=%lu discharge_us=%lu voltage_us=%lu logo_us=%lu\n",
        pair?"other":"allied",(unsigned long)(afterPolarity-began),
        (unsigned long)(afterDischarge-afterPolarity),(unsigned long)(afterVoltage-afterDischarge),
        (unsigned long)(afterLogo-afterVoltage));
    }
    std::memcpy(screen,base,kBytes);mode=saved;
  }
  bool begin(uint16_t *lcdBuffer){
    screen=lcdBuffer;
    partition=esp_partition_find_first(ESP_PARTITION_TYPE_DATA,ESP_PARTITION_SUBTYPE_DATA_FAT,"ffat");
    if(!partition||!read(0,&header,sizeof(header))||
       std::memcmp(header.magic,"LIVE50__",8)||header.version!=1||header.width!=240||
       header.fps!=50||header.frames!=311||header.payloadOffset!=4096||
       header.payloadBytes>partition->size-header.payloadOffset){
      Serial.println("DISPLAY_ERROR: LIVE50 asset missing or incompatible");return false;
    }
    base=static_cast<uint16_t*>(heap_caps_malloc(kBytes,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
    voltageLayer=static_cast<uint16_t*>(heap_caps_malloc(kBytes,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
    voltagePixels=static_cast<VoltagePixel*>(heap_caps_malloc(176*80*sizeof(VoltagePixel),
      MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
    compressed=static_cast<uint8_t*>(heap_caps_malloc(kMaxCompressed,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
    delta=static_cast<uint8_t*>(heap_caps_malloc(kBytes,MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT));
    if(!base||!voltageLayer||!voltagePixels||!compressed||!delta){
      Serial.println("DISPLAY_ERROR: optical buffers unavailable");return false;
    }
    std::memset(screen,0,kBytes);requests=xQueueCreate(1,sizeof(Request));results=xQueueCreate(1,sizeof(Response));
    if(!requests||!results||xTaskCreatePinnedToCore(workerEntry,"liveDecode",24576,this,1,nullptr,1)!=pdPASS){
      Serial.println("DISPLAY_ERROR: optical decoder task");return false;
    }
    if(!enqueue(0))return false;
    Response initial;if(!take(initial))return false;apply(initial);
    if(!enqueue(1))return false;pending=1;
    LCD_1IN28_Display(screen);
    DEV_SET_Backlight(80);nextUs=micros()+kFrameUs;reportAt=millis();frames=1;
    Serial.println("DISPLAY_READY: LIVE_OPTICS50 240x240 RGB565, measured voltage and pin state");
    return true;
  }
  bool tick(const tester::Result &reading){
    const bool active=(reading.state==tester::State::Supply||reading.state==tester::State::OverRange)&&
      reading.positiveMask&&reading.returnMask&&std::isfinite(reading.volts);
    const bool recognized=(reading.positiveMask|reading.returnMask)==3;
    if(active&&(mode==IDLE||mode==WITHDRAW)){if(!select(INSERT))return false;}
    else if(!active&&(mode==POWERED||mode==RECOGNIZED||mode==INSERT)){if(!select(WITHDRAW))return false;}
    else if(active&&mode==POWERED&&recognized){if(!select(RECOGNIZED))return false;}
    else if(active&&mode==RECOGNIZED&&!recognized){if(!select(POWERED))return false;}
    if(int32_t(micros()-nextUs)<0){delay(1);return true;}
    Response ready;if(!take(ready))return false;
    if(ready.index!=pending){Serial.println("DISPLAY_ERROR: out-of-order live frame");return false;}
    if(mode==INSERT&&pending>=155&&!separate){
      std::memcpy(base,screen,kBytes);separate=true;
    }
    apply(ready);show(ready,reading);
    uint16_t next=pending+1;
    if(next==end(mode)){
      if(mode==INSERT){
        Serial.printf("DISPLAY_INSERT_DONE duration_ms=%lu frames=21\n",
          (unsigned long)(millis()-insertStartedAt));
        mode=recognized?RECOGNIZED:POWERED;
      }
      else if(mode==WITHDRAW)mode=IDLE;
      next=first(mode);
    }
    pending=next;if(!enqueue(pending))return false;
    nextUs+=kFrameUs;
    if(int32_t(micros()-nextUs)>kFrameUs)nextUs=micros();
    const uint32_t now=millis();
    if(now-reportAt>=5000){
      const uint32_t count=frames-lastFrames,elapsed=now-reportAt;
      Serial.printf("DISPLAY_ALIVE mode=%s fps_x10=%lu decode_us=%lu overlay_us=%lu transfer_us=%lu free_heap=%u\n",
        name(mode),
        (unsigned long)(count*10000UL/elapsed),(unsigned long)(count?decodeTime/count:0),
        (unsigned long)(count?overlayTime/count:0),(unsigned long)(count?transferTime/count:0),ESP.getFreeHeap());
      Serial.printf("DISPLAY_BENCH_CACHE allied_us=%lu other_us=%lu allied_discharge_us=%lu other_discharge_us=%lu voltage_us=%lu\n",
        (unsigned long)benchPair[0],(unsigned long)benchPair[1],
        (unsigned long)benchDischarge[0],(unsigned long)benchDischarge[1],
        (unsigned long)benchVoltage[0]);
      reportAt=now;lastFrames=frames;decodeTime=overlayTime=transferTime=0;
    }
    return true;
  }
};
}  // namespace live_optics
