# 기말 텀프
# Thermostate 보일러 온도 측정 및 target 설정

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

sensor = dht.DHT22(Pin(17))

rotaryA = Pin(43, Pin.IN, Pin.PULL_UP)
rotaryB = Pin(44, Pin.IN, Pin.PULL_UP)

old_encode = 0
right = [13, 32, 20, 01]
left = [10, 02, 23, 31]

temerature = 0
humidity = 0
value = 0
def rotated(p):
    global old_encode, value, lastPub
    new_state = rotaryA.value() << 1| rotaryB.value()
    if new_state != old_encode:
        new_combined = old_encode * 10 + new_state
        old_encode = new_state
        if new_combined in right:
            value = (value + 1) if value < 255 else 255
        elif new_combined in left:
            value = (value - 1) if value > 0 else 0
        lastPub = time.ticks_ms() - device.meta['pubInterval'] + 50
        display()

rotaryA.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=rotated)
rotaryB.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=rotated)

tft = tft_config.config(3, buffer_size=64*64*2)

tft.init()
tft.fill(st7789.BLACK)
tft.text(font2, 'Thermostat', 85, 5, st7789.WHITE)
tft.text(font1, 'Target      : ', 65, 50, st7789.WHITE)
tft.text(font1, 'Temperature : ', 65, 80, st7789.WHITE)
tft.text(font1, 'Humidity    : ', 65, 110, st7789.WHITE)

def r2t(r):
    # 0.1960784 = (60 - 10) / 255 - 0
    return r * 0.1960784 + 10

def t2r(t):
    # 0.1960784 = (60 - 10) / 255 - 0
    # 
    return (t - 10) / 0.1960784

lastMeasured = -2001
def measureData():
    global temperature, humidity, lastMeasured
    if (time.ticks_ms() - 2000) > lastMeasured:
        lastMeasured = time.ticks_ms()
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        display()

def handleCommand(topic, msg):
    global lastPub, value
    jo = json.loads(str(msg,'utf8'))
    if ("target" in jo['d']):
        value = t2r(int(jo['d']['target']))
        lastPub = - device.meta['pubInterval']
        display()
        
def display():
    tft.text(font1, f'{round(r2t(value),2)}', 200, 50, st7789.WHITE)
    tft.text(font1, f'{round(temperature, 2)}', 200, 80, st7789.WHITE)
    tft.text(font1, f'{round(humidity, 2)}', 200, 110, st7789.WHITE)
    
nic = uComMgr32.startWiFi('io7thermostat')
device = ConfiguredDevice()
device.setUserCommand(handleCommand)

device.connect()

lastPub = time.ticks_ms() - device.meta['pubInterval']

while True:
    if not device.loop():
        tft.deinit()
        break
    measureData()
    if (time.ticks_ms() - device.meta['pubInterval']) > lastPub:
        lastPub = time.ticks_ms()
        device.publishEvent('status',
            json.dumps({
                'd' : {
                        'target': round(r2t(value),2),
                        'temperature' : round(temperature, 2),
                        'humidity' : round(humidity, 2),
                      }
                 }
            )
        )
