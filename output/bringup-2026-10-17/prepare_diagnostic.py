from pathlib import Path
import shutil
root=Path(__file__).resolve().parent
source=root.parents[1]/'firmware/Tester12VRevD'
target=root/'BoardDiagnostic';target.mkdir(exist_ok=True)
for name in ['DEV_Config.cpp','DEV_Config.h','Debug.h','LCD_1in28.cpp','LCD_1in28.h','Measurement.h']:
 shutil.copyfile(source/name,target/name)
s=(source/'Tester12VRevD.ino').read_text()
inject=r'''
// Diagnostic-only build: no terminal stimulus and no automatic calibration.
static unsigned diagnosticFaults=0;
void diagnosticScan() {
  Serial.printf("BUS_LEVELS SDA=%d SCL=%d clock=100000\n", digitalRead(DEV_SDA_PIN),digitalRead(DEV_SCL_PIN));
  unsigned adcCount=0,total=0;
  for(uint8_t address=8;address<120;address++) {
    Wire.beginTransmission(address);
    const uint8_t error=Wire.endTransmission();
    if(error==0) {
      Serial.printf("I2C_FOUND address=0x%02X\n",address);total++;
      if(address>=0x48&&address<=0x4B)adcCount++;
    } else if(error!=2) {
      Serial.printf("I2C_ERROR address=0x%02X error=%u\n",address,error);
    }
  }
  Serial.printf("I2C_SCAN_END devices=%u adc_addresses=%u expected_adc_addresses=4\n",total,adcCount);
}
'''
s=s.replace('bool writeReg(uint8_t address',inject+'\nbool writeReg(uint8_t address',1)
s=s.replace('return Wire.endTransmission()==0;',r'''const uint8_t error=Wire.endTransmission();
  if(error && diagnosticFaults++<16) Serial.printf("ADC_WRITE_ERROR address=0x%02X register=%u error=%u SDA=%d SCL=%d\n",address,reg,error,digitalRead(DEV_SDA_PIN),digitalRead(DEV_SCL_PIN));
  return error==0;''',1)
s=s.replace('if (Wire.endTransmission(false)!=0) return false;',r'''const uint8_t error=Wire.endTransmission(false);
  if(error) { if(diagnosticFaults++<16)Serial.printf("ADC_POINTER_ERROR address=0x%02X register=%u error=%u\n",address,reg,error);return false; }''',1)
s=s.replace('if (Wire.requestFrom(address,(uint8_t)2)!=(uint8_t)2) return false;',r'''const uint8_t count=Wire.requestFrom(address,(uint8_t)2);
  if(count!=2) {if(diagnosticFaults++<16)Serial.printf("ADC_READ_ERROR address=0x%02X register=%u received=%u\n",address,reg,count);return false;}''',1)
s=s.replace('if(!readReg(0x48+bank,1,status)||(status&0x7fff)!=(setting&0x7fff))return false;',r'''if(!readReg(0x48+bank,1,status))return false;
        if((status&0x7fff)!=(setting&0x7fff)) {
          if(diagnosticFaults++<16)Serial.printf("ADC_CONFIG_ERROR address=0x%02X got=%04X expected=%04X\n",0x48+bank,status,setting);
          return false;
        }''',1)
s=s.replace('if(!std::isfinite(volts)||volts<.20f||volts>.98f)return false;',r'''if(!std::isfinite(volts)||volts<.20f||volts>.98f) {
          if(diagnosticFaults++<16)Serial.printf("ADC_RANGE_ERROR address=0x%02X channel=%u volts=%.7f code=%04X\n",0x48+bank,channel,volts,code);
          return false;
        }''',1)
s=s.replace('Serial.println("TESTER12V Rev D: real ADC input; + and - indicate relative polarity only");','Serial.println("TESTER12V Rev D DIAGNOSTIC: real ADC input; no calibration commands sent");\n  diagnosticScan();',1)
s=s.replace('void loop() {','void loop() {\n  static uint32_t lastScan=millis();\n  if(millis()-lastScan>5000){diagnosticScan();lastScan=millis();}',1)
assert 'ADC_WRITE_ERROR' in s and 'ADC_CONFIG_ERROR' in s and 'ADC_RANGE_ERROR' in s
(target/'BoardDiagnostic.ino').write_text(s)
print(target)
