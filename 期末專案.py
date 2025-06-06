import machine
import dht
import time
import gc
import network
import urequests
from machine import Pin, I2C, PWM, ADC
from ssd1306 import SSD1306_I2C
from font_HunInn import font_HunInn
import framebuf

SSID = 'AndroidAPAC2E'
PASSWORD = '77777777'
BOT_TOKEN = '7928381094:AAH6g9SECfRTDLq8x5S_Uu0JHByrmDCKEOM'
CHAT_ID = '7207428159'

sensor = dht.DHT11(Pin(15))
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = SSD1306_I2C(128, 64, i2c)
buzzer = PWM(Pin(14))
buzzer.duty(0)
red_led = Pin(16, Pin.OUT)
green_led = Pin(13, Pin.OUT)
green_led.on()
pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)
button_a = Pin(5, Pin.IN, Pin.PULL_UP)

def draw_chinese(oled, text, x, y):
    for i, ch in enumerate(text):
        data = font_HunInn.get(ch)
        if data:
            fb = framebuf.FrameBuffer(bytearray(data), 16, 16, framebuf.MONO_HLSB)
            oled.blit(fb, x + i * 16, y)

def draw_big_number(oled, number_str, x, y):
    for i, ch in enumerate(number_str):
        data = font_HunInn.get(ch)
        if data:
            fb = framebuf.FrameBuffer(bytearray(data), 16, 16, framebuf.MONO_HLSB)
            oled.blit(fb, x + i * 16, y)

def send_temp_alert(temp, hum, threshold):
    msg = (
        "🚨（高溫警報）🚨\n"
        f"目前溫度：{temp}°C\n"
        f"目前濕度：{hum}%\n"
        f"警報門檻：{threshold}°C\n"
        "⚠️ 已超過設定溫度，請注意環境狀況！"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        gc.collect()
        data = ('chat_id=' + str(CHAT_ID) + '&text=' + msg).encode('utf-8')
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        r = urequests.post(url, data=data, headers=headers)
        print("📨 Telegram 已發送高溫警報")
        r.close()
    except Exception as e:
        print("⚠️ Telegram 傳送失敗:", e)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    timeout = 15
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
    return wlan.isconnected()

max_temp = -999
min_temp = 999
min_hum = 999
警報門檻 = 29
頁面 = 1
mute = False
last_button_state = 1
已通知 = False

if connect_wifi():
    print("✅ WiFi 已連線")
else:
    print("❌ WiFi 連線失敗")

while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        if temp > max_temp:
            max_temp = temp
        if temp < min_temp:
            min_temp = temp
        if hum < min_hum:
            min_hum = hum

        button_state = button_a.value()
        if last_button_state == 1 and button_state == 0:
            mute = not mute
            print("🔇 靜音狀態:", mute)
        last_button_state = button_state

        if temp >= 警報門檻:
            for _ in range(3):
                if not mute:
                    buzzer.freq(1000)
                    buzzer.duty(512)
                red_led.on()
                time.sleep(0.2)
                buzzer.duty(0)
                red_led.off()
                time.sleep(0.2)
            if not 已通知:
                send_temp_alert(temp, hum, 警報門檻)
                已通知 = True
        else:
            buzzer.duty(0)
            red_led.off()
            已通知 = False

        pot_value = pot.read()
        delay_time = 0.03 + (0.5 - 0.03) * (1 - pot_value / 4095)

        for shift in range(64, -1, -4):
            oled.fill(0)
            temp_fb = framebuf.FrameBuffer(bytearray(128 * 64), 128, 64, framebuf.MONO_HLSB)

            if 頁面 == 1:
                draw_chinese(temp_fb, "溫度:", 0, 16)
                draw_big_number(temp_fb, str(temp), 70, 16)
                draw_chinese(temp_fb, "°C", 100, 16)
                draw_chinese(temp_fb, "濕度:", 0, 36)
                draw_big_number(temp_fb, str(hum), 70, 36)
                draw_chinese(temp_fb, "%", 110, 36)
            elif 頁面 == 2:
                draw_chinese(temp_fb, "最高溫:", 0, 16)
                draw_big_number(temp_fb, str(max_temp), 70, 16)
                draw_chinese(temp_fb, "°C", 100, 16)
                draw_chinese(temp_fb, "最低溫:", 0, 36)
                draw_big_number(temp_fb, str(min_temp), 70, 36)
                draw_chinese(temp_fb, "°C", 100, 36)
            elif 頁面 == 3:
                draw_chinese(temp_fb, "高溫警報!!" if temp >= 警報門檻 else "溫度正常~~", 16, 24)

            oled.blit(temp_fb, 0, -shift)
            oled.show()
            time.sleep(delay_time)

        print(f"🌡️ 溫度: {temp}°C, 💧 濕度: {hum}%")

    except OSError:
        print("❌ 無法讀取 DHT11 感測器")

    頁面 += 1
    if 頁面 > 3:
        頁面 = 1

    time.sleep(0.5)