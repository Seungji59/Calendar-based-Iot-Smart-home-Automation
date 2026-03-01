## 외부 날씨 받아와서 디스플레이에 나타내기

from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin, ADC, Timer
import st7789
import tft_config
import vga2_8x16 as font1
import vga1_bold_16x32 as font2
import dht


# ---------------------------
# TFT 초기화
# ---------------------------
tft = tft_config.config(3, buffer_size=64*64*2)
tft.init()
tft.fill(st7789.BLACK)

# 초기 화면
tft.text(font2, 'Weather Info', 60, 5, st7789.WHITE)
tft.text(font1, 'Temperature : ', 50, 50, st7789.WHITE)
tft.text(font1, 'Weather     : ', 50, 80, st7789.WHITE)

# ---------------------------
# 변수 초기화
# ---------------------------
weather = 0.0
outside_temp = '--'

def handleCommand(topic, msg):
    global weather, outside_temp
    jo = json.loads(str(msg,'utf8'))

    # 'd' 안 붙어 있어도 처리
    if "d" in jo:
        data = jo['d']
    else:
        data = jo

    if "weather" in data and "temp" in data:
        weather = data['weather']
        outside_temp = data['temp']
        display()
 
def display():
    # 필요하면 영역만 지우기
    tft.fill_rect(200, 50, 60, 16, st7789.BLACK)   # Temperature 영역
    tft.fill_rect(200, 80, 60, 16, st7789.BLACK)   # Weather 영역
    
    # 제목
    tft.text(font2, 'Weather Info', 60, 5, st7789.WHITE)

    # 외부 온도 표시
    tft.text(font1, 'Temperature : ', 50, 50, st7789.WHITE)
    tft.text(font1, f'{round(outside_temp,2)} C', 200, 50, st7789.WHITE)

    # 날씨 상태 표시
    tft.text(font1, 'Weather     : ', 50, 80, st7789.WHITE)
    tft.text(font1, f'{weather}', 200, 80, st7789.WHITE)


# ---------------------------
# Wi-Fi 연결
# ---------------------------
nic = uComMgr32.startWiFi('io7thermostat')
device = ConfiguredDevice()
device.setUserCommand(handleCommand)

device.connect()

lastPub = time.ticks_ms() - device.meta['pubInterval']

# ---------------------------
# 메인 루프
# ---------------------------
while True:
    if not device.loop():
        tft.deinit()
        break
    if (time.ticks_ms() - device.meta['pubInterval']) > lastPub:
        lastPub = time.ticks_ms()
    
        device.publishEvent('status',
    json.dumps({
        'd' : {
                'temp': str(outside_temp),  # 문자열 그대로
                'weather' : weather,
              }
         }
    )
)


