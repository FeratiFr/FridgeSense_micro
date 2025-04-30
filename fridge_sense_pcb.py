import network
import urequests
import machine
from time import gmtime
import socket
import struct
import neopixel
import esp32
import time
import json
import sys
# import de2120_barcode_scanner
from machine import Pin, deepsleep, ADC, PWM, UART

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    if(machine.wake_reason() == machine.EXT1_WAKE):
        print("EXT0 Wake up")

photo_resistor = ADC(Pin(5))
photo_resistor.atten(ADC.ATTN_11DB)
# Supabase API details
SUPABASE_URL = "https://wyzjemwyznhgrbosfoqc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5emplbXd5em5oZ3Jib3Nmb3FjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NjcxMjEsImV4cCI6MjA2MTQ0MzEyMX0.PoEf5f6t8A-hFVUNf5PFlekCW4wT_s6MvrgJu69NwR4"
SUPABASE_TABLE = "modeState"  # Replace with your table name

# Headers for Supabase authentication
HEADERS = {
    "Accept": "application/json",  # Add this to explicitly accept JSON responses
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

#hardware init
buzzer = PWM(Pin(6), freq= 2400, duty = 0)
button = Pin(7, Pin.IN, Pin.PULL_UP)
# ssid = "seguns_iPhone"
# password = "Br0c0ll1"


def connect_to_wifi(ssid, password):
    wifi = network.WLAN(network.STA_IF)
    wifi.active(False)
    time.sleep(1)
    wifi.active(True)
    wifi.connect(ssid, password)
    
    
    # Wait for connection
    for _ in range(10):  # Try for 10 seconds
        if wifi.isconnected():
            print("connected to wifi")
            return True
        time.sleep(1)
    return False

#access point stuff START
def ap_mode():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP32-Config", password="12345678")  # AP credentials
    print("Access Point started. Connect to SSID:", ap.ifconfig()[0])
    
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    s.bind(addr)
    s.listen(1)
    print("Web server started on http://192.168.4.1")

    html = """<!DOCTYPE html>
    <html>
    <head><title>Wi-Fi Configuration</title></head>
    <body>
    <h1>ESP32 Wi-Fi Configuration</h1>
    <form action="/" method="post">
      SSID: <input type="text" name="ssid"><br>
      Password: <input type="password" name="password"><br>
      <input type="submit" value="Connect">
    </form>
    </body>
    </html>"""
    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024)
        request = str(request)

        # Check if the form was submitted
        if "POST /" in request:
            # Extract SSID and password from the request
            ssid_start = request.find("ssid=") + 5
            ssid_end = request.find("&", ssid_start)
            ssid = request[ssid_start:ssid_end]

            password_start = request.find("password=") + 9
            password_end = request.find(" ", password_start)
            password = request[password_start:password_end]

            print("Received Wi-Fi credentials:")
            print("SSID:", ssid)
            print("Password:", password)
            
            try:
                with open("wifi_config.txt", "w") as f:  # Open file in write mode
                    f.write(ssid + "\n")  # Store SSID on the first line
                    f.write(password + "\n")  # Store password on the second line
                print("Wi-Fi credentials saved successfully.")
            except OSError as e:
                print("Error saving Wi-Fi credentials:", e)

            # Try to connect to the Wi-Fi network
            if connect_to_wifi(ssid, password):
                response = "Connected to Wi-Fi! IP: " + network.WLAN(network.STA_IF).ifconfig()[0]
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                conn.send(response)
                conn.close()
                print("Connected to Wi-Fi") #get rid of this after testing phase
                break
                
            else:
                response = "Failed to connect to Wi-Fi. Please try again."

            conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            conn.send(response)
        else:
            # Serve the HTML form
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            conn.send(html)

        conn.close()
#access point stuff END

def read_wifi_credentials():
    try:
        with open("wifi_config.txt", "r") as f:  # Open file in read mode
            lines = f.readlines()
            ssid = lines[0].strip()  # Read first line (SSID)
            password = lines[1].strip()  # Read second line (Password)
        return ssid, password
    except OSError:
        print("Wi-Fi credentials file not found.")
        return None, None  # Return None if file is missing

#send data to superbase
def send_data(mode,barcode):
    """Sends mode and state data to Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
    data = {"mode": mode, "barcode": str(barcode)}

    try:
        response = urequests.post(url, json=data, headers=HEADERS)
        print("Supabase Response:", response.text)
        response.close()
    except Exception as e:
        print("Error:", e)

#provide audio cue
def buzz(m):
    buzzer.duty(128)
    if m == 0:
        buzzer.freq(3600)
        buzzer.duty(256)
    elif m == 1:
        buzzer.freq(1200)
    elif m == 2:
        buzzer.freq(2000)
    else:
        buzzer.freq(2400)
    
    
    time.sleep(0.2)
    buzzer.duty(0)
    
# connect_to_wifi(ssid,password)
# send_data(0,"012345678")

ssid, password = read_wifi_credentials()
if ssid and password:
    if connect_to_wifi(ssid,password):
        print("Connected to Wi-Fi: ",ssid)
    else:
        print("Starting AP mode")
        ap_mode()
else:
    print ("Starting AP mode")
    ap_mode()

debouncing_array = [1] * 2
button_press_n = [1,1]

#scanner init
uart = UART(1, baudrate =115200, tx= 8, rx = 7)
def clear_serial_buffer(uart):
     while uart.any():
         uart.read()

my_scanner = de2120_barcode_scanner.DE2120BarcodeScanner()
clear_serial_buffer(uart)

def button_read(t):
#     print (button.value())
    global button_press_n
#     global mode
    debouncing_array.append(button.value())
    debouncing_array.pop(0)
    #print(debouncing_array)
    if(debouncing_array != button_press_n):
        if(mode == 0):
            mode = 1
            print("mode switch from output to input")
            buzz(0)
            buzz(1)
        elif(mode == 1):
            mode = 0
            print("mode switch from input to output")
            buzz(1)
            buzz(0)

sleep = 0
#prev_sleep = 0
def light_barcode_read(t):
#     global state
#     global mode
    #print("mode: ",mode, "state: ",state)
    #send_data(state,mode)
    radiance = photo_resistor.read()
    global sleep
    
    if(radiance < 100): #no light detected condition
        #state = 0
#         send_data(mode,state)
#         time.sleep(2)
        if(sleep == 0):
            sleep = 1
            print("no light detected. sleeping. radiance = ",radiance) #comment this out after testing
        #time.sleep(15)
#         machine.lightsleep()
    else:
        if(sleep == 1):
            sleep = 0
            print("waking up from deepsleep")
    my_scanner.start_scan()
    barcode = my_scanner.read_barcode()
    if(barcode):
        print(barcode)
        #my_scanner.stop_scan()
        send_data(mode,barcode)

pin5 = Pin(0, Pin.IN)
esp32.wake_on_ext1(pins=(pin5,), level=esp32.WAKEUP_ANY_HIGH)

tim2 = machine.Timer(0)
tim2.init(period = 10, mode = machine.Timer.PERIODIC, callback = button_read)

tim1= machine.Timer(1)
tim1.init(period = 1000, mode = machine.Timer.PERIODIC, callback = light_barcode_read)

