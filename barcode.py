import de2120_barcode_scanner
import machine
from machine import Pin, deepsleep, ADC, PWM, UART
import time


mode = 1
uart = UART(1, baudrate =115200, tx= 21, rx = 20) #change pin no.
def clear_serial_buffer(uart):
     while uart.any():
         uart.read()

my_scanner = de2120_barcode_scanner.DE2120BarcodeScanner() #change pin no. in library
uart = UART(1, baudrate =115200, tx= 21, rx = 20) #change pin no.
clear_serial_buffer(uart)
my_scanner.send_command("SCMMAN")

my_scanner.is_connected()
time.sleep(0.5)
if(my_scanner.is_connected()):
    print("barcode scanner is online")
else:

    print("barcode scanner not found")

def barcode_read(t):
    my_scanner.start_scan()
    #time.sleep(1.5)
    barcode = my_scanner.read_barcode()
    if(barcode):
        print(barcode)
        #my_scanner.stop_scan()
        #send_data(mode,barcode)
        
tim1= machine.Timer(1)
tim1.init(period = 2000, mode = machine.Timer.PERIODIC, callback = barcode_read)
