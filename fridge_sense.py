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
from machine import Pin, deepsleep, ADC, PWM


def connect_to_wifi(ssid, password):
    wifi = network.WLAN(network.STA_IF)
    wifi.active(False)
    time.sleep(1)
    wifi.active(True)
    wifi.connect(ssid, password)
    
    
    # Wait for connection
    for _ in range(10):  # Try for 10 seconds
        if wifi.isconnected():
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


#firebase stuff START
FIREBASE_URL = "https://fridgesense-e1c59-default-rtdb.firebaseio.com/.json"

def send_data(mode, state):
    data = {"mode": mode,
            "state": state}
    try:
        response = urequests.post(FIREBASE_URL, json=data)
        #print("Response:", response.text)
        response.close()
    except Exception as e:
        print("Error:", e)
        
#test
#send_data(1,0)
#test successful
#firebase stuff END

# ssid, password = read_wifi_credentials()
# if ssid and password:
#     if connect_to_wifi(ssid,password):
#         print("Connected to Wi-Fi: ",ssid)
#     else:
#         print("Starting AP mode")
#         ap_mode()
# else:
#     print ("Starting AP mode")
#     ap_mode()

button = Pin(12, Pin.IN, Pin.PULL_DOWN)

buzzer = PWM(Pin(33), freq= 2400, duty = 0)


photo_resistor = ADC(Pin(32))
photo_resistor.atten(ADC.ATTN_11DB)
#about 2900 under normal light conditons in the lab
#way less than 1000 when covered up

debouncing_array = [0] * 5

mode = 0 #input mode default
state = 1 #on state default


if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    if(machine.wake_reason() == machine.EXT0_WAKE):
        #send_data(1,mode)
        print("EXT0 Wake up")
        send_data(mode,1)
                

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

def debounce():
    time.sleep(0.001)
    return

def light_read(t):
    global state
    global mode
    #print("mode: ",mode, "state: ",state)
    #send_data(state,mode)
    radiance = photo_resistor.read()
    #print(radiance)
    if(radiance < 200): #no light detected condition
        state = 0
        #send_data(state,mode)
        time.sleep(2)
        print("no light detected. sleeping") #comment this out after testing
        #time.sleep(15)
        deepsleep()
        
def switchPress(pin):
    global mode
    global state
    #update mode if button is pressed
    if(mode == 0):
        mode = 1
        print("mode switch from input to output")
    elif(mode == 1):
        mode = 0
        print("mode switch from output to input")
    
    
button_press = [0,0,0,0,1]


def button_read(t):
    global button_press
    global mode
    debouncing_array.append(button.value())
    debouncing_array.pop(0)
    #print(debouncing_array)
    if(debouncing_array == button_press):
        if(mode == 0):
            mode = 1
            print("mode switch from input to output")
            buzz(0)
        elif(mode == 1):
            mode = 0
            print("mode switch from output to input")
            buzz(1)
        #send_data(mode,1)

    

#def tim2_callback(t):
    #print("I am going to sleep for 1 minute.")
    #machine.deepsleep(60000)
    
esp32.wake_on_ext0(pin=Pin(32), level=esp32.WAKEUP_ANY_HIGH)
#test with a smaller resistor value because fridge lighting conditions may not match lab conditons

tim2 = machine.Timer(2)
tim2.init(period = 10, mode = machine.Timer.PERIODIC, callback = button_read)

tim1 = machine.Timer(1)
tim1.init(period = 1000, mode = machine.Timer.PERIODIC, callback = light_read)



#button.irq(handler= switchPress, trigger=Pin.IRQ_RISING)

