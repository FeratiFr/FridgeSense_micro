import de2120_barcode_scanner
from machine import Pin, deepsleep, ADC, PWM, UART
import time

uart = UART(1, baudrate =9600, tx= Pin(21), rx = Pin(20))
def clear_serial_buffer(uart):
     while uart.any():
         uart.read()

my_scanner = de2120_barcode_scanner.DE2120BarcodeScanner()
clear_serial_buffer(uart)

print(my_scanner.begin())

while True:
    print(my_scanner.is_connected())
    time.sleep(0.2)