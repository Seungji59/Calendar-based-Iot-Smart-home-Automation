# 기말 텀프
# Valve (보일러)  + Trip 기능 추가

from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32

# -----------------------------
# 소프트웨어 상태 변수
# -----------------------------
trip_state = "untrip"   # 초기 상태

# -----------------------------------------------------------
# MQTT로 들어오는 명령(Command)을 처리하는 콜백 함수
# topic : 들어온 MQTT topic
# msg   : payload (바이트 형태로 들어옴)
# -----------------------------------------------------------
def handleCommand(topic, msg):
    global lastPub, trip_state
    jo = json.loads(str(msg,'utf8'))
    if ("valve" in jo['d']):
        if jo['d']['valve'] == 'on':
            valve.on()
        else:
            valve.off()
        lastPub = - device.meta['pubInterval'] # 이벤트 즉시 publish 할 수 있도록 lastPub 조정
        
    if ("trip" in jo['d']):
        # 들어온 값 그대로 저장 (예: trip / untrip)
        trip_state = jo['d']['trip']

# -----------------------------------------------------------
# 네트워크 및 장치 설정
# -----------------------------------------------------------
nic = uComMgr32.startWiFi('valve')
device = ConfiguredDevice()
device.setUserCommand(handleCommand)

device.connect()

from machine import Pin
valve = Pin(15, Pin.OUT)
lastPub = time.ticks_ms() - device.meta['pubInterval']

# -----------------------------------------------------------
# 메인 Loop
# -----------------------------------------------------------
while True:
    # device.loop() : MQTT 수신 처리 및 keep-alive 유지
    # false를 반환하면 연결이 끊어진 것 → 종료 0
    if not device.loop():
        break
    # pubInterval 마다 현재 밸브 상태를 주기적으로 publish
    if (time.ticks_ms() - device.meta['pubInterval']) > lastPub:
        lastPub = time.ticks_ms()
        
        # valve.value()는 1 또는 0 → 이를 "on", "off" 문자열로 변환
        # Node-RED에서 사용할 상태 JSON
        status_data = {
            'd': {
                'valve': 'on' if valve.value() else 'off',
                'trip': trip_state   # ★ 하드웨어 X → 변수로 저장된 값 전달
            }
        }

        device.publishEvent('status', json.dumps(status_data))
