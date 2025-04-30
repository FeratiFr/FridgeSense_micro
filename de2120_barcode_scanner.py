#-----------------------------------------------------------------------------
# de2120_barcode_scanner.py
#
# Python library for the SparkFun 2D Barcode Scanner Breakout.
# https://www.sparkfun.com/products/18088
#
#------------------------------------------------------------------------
# Written by Priyanka Makin @ SparkFun Electronics, April 2021
#
# Do you like this library? Help support SparkFun. Buy a board!
#==================================================================================
# Copyright (c) 2020 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.
#==================================================================================

"""
de2120_barcode_scanner
============
Python module for the 2D Barcode Scanner.

This python package is a port of the exisiting [SparkFun DE2120 Arduino Library](https://github.com/sparkfun/SparkFun_DE2120_Arduino_Library)

"""
#-----------------------------------------------------------------------------------

import time
from machine import UART

_DEFAULT_NAME = "DE2120 Barcode Scanner"

class DE2120BarcodeScanner(object):
    """
    DE2120BarcodeScanner 

    Initialize the library with the given UART interface.

    :param uart:   The UART interface to use to communicate with the module, this
                   is a UART interface at 9600 baud rate.

    :return:       The DE2120BarcodeScanner object.
    :rtype:        Object
    """
    # Constructor
    device_name = _DEFAULT_NAME
    
    # DE2120 response
    DE2120_COMMAND_ACK = 0x06
    DE2120_COMMAND_NACK = 0x15

    # Send commands
    # Need to prepend "^_^" and append "."
    COMMAND_START_SCAN = "SCAN"
    COMMAND_STOP_SCAN = "SLEEP"
    COMMAND_SET_DEFAULTS = "DEFALT"
    COMMAND_GET_VERSION = "DSPYFW"

    PROPERTY_BUZZER_FREQ = "BEPPWM"
    PROPERTY_DECODE_BEEP = "BEPSUC"
    PROPERTY_BOOT_BEEP = "BEPPWR"
    PROPERTY_FLASH_LIGHT = "LAMENA"
    PROPERTY_AIM_LIGHT = "AIMENA"
    PROPERTY_READING_AREA = "IMGREG"
    PROPERTY_MIRROR_FLIP = "MIRLRE"
    PROPERTY_USB_DATA_FORMAT = "UTFEAN"
    PROPERTY_SERIAL_DATA_FORMAT = "232UTF"
    PROPERTY_INVOICE_MODE = "SPCINV"
    PROPERTY_VIRTUAL_KEYBOARD = "KBDVIR"
    PROPERTY_COMM_MODE = "POR"
    PROPERTY_BAUD_RATE = "232BAD"
    PROPERTY_READING_MODE = "SCM"
    PROPERTY_CONTINUOUS_MODE_INTERVAL = "CNTALW"
    PROPERTY_MOTION_SENSITIVITY = "MDTTHR"
    PROPERTY_TRANSFER_CODE_ID = "CIDENA"
    PROPERTY_KBD_CASE_CONVERSION = "KBDCNV"
    PROPERTY_ENABLE_ALL_1D = "ODCENA"
    PROPERTY_DISABLE_ALL_1D = "ODCDIS"
    PROPERTY_ENABLE_ALL_2D = "AQRENA"
    PROPERTY_DISABLE_ALL_2D = "AQRDIS"

    def __init__(self, uart=None):
        """
        Initialize the DE2120 Barcode Scanner with a UART interface.

        :param uart: UART interface object. If None, it assumes the UART is already initialized.
        """
        self.uart = UART(1, baudrate =9600, tx= 21, rx = 20)

    def begin(self):
        """
        Initializes the device with basic settings. Calls the is_connected() function.

        :return: Returns true if initialization was successful.
        :rtype: bool
        """
        if not self.is_connected():
            return False
        
        # Clear any remaining incoming chars. This prevents a mis-read
        # of the first barcode
        self.uart.flush()

        # We're all setup
        return True

    def is_connected(self):
        """
        Ask the DE2120 for the firmware version.

        :return: Returns true if the DE2120 responds with an ACK.
        :rtype: bool
        """
        # Try sending the firmware version command
        write_string = "^_^" + chr(4) + "SPYFW."
        print("Sending ",write_string.encode())
        self.uart.write(write_string.encode())
        
        # Now, look for module response
        # If it's an ACK, return true
        # Otherwise, return false
        incoming = self.uart.read(1)
        print("incoming",incoming)
        if incoming and ord(incoming) == self.DE2120_COMMAND_ACK:
            return True
        elif incoming and ord(incoming) == self.DE2120_COMMAND_NACK:
            return False
        else:
            return False

    def factory_default(self):
        """
        Send command to put the module back into factory default settings.

        :return: True if command successfully received, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.COMMAND_SET_DEFAULTS)

    def available(self):
        """
        :return: the number of bytes in the UART receive buffer.
        :rtype: int
        """
        return self.uart.any()

    def read(self):
        """
        :return: the first byte on the UART port.
        :rtype: int
        """
        return self.uart.read(1)

    def send_command(self, cmd, arg=""):
        """
        Create command string and send to DE2120 over UART.

        :param cmd: The command name.
        :param arg: The command variation, if there is one.
        :return: True if the response from DE2120 contains the ACK character, false otherwise.
        :rtype: bool
        """
        start = '^_^'
        end = '.'
        command_string = start + cmd + arg + end
        
        #print("sending", command_string.encode())
        self.uart.write(command_string.encode())
        
        incoming = self.uart.read(1)
        if incoming and ord(incoming) == self.DE2120_COMMAND_ACK:
            return True
        elif incoming and ord(incoming) == self.DE2120_COMMAND_NACK:
            return False
        return False

    def read_barcode(self):
        """
        Read from the UART buffer until we hit a new line character.

        :return: the string in the UART buffer.
        :rtype: str
        """
        if not self.uart.any():
            return False
        
        incoming = self.uart.readline()
        return incoming.decode()

    def change_baud_rate(self, baud):
        """
        Change the UART baud rate for the barcode module.

        :param baud: baud rate to change to.
        :return: true if command is successfully sent, false otherwise.
        :rtype: bool
        """
        baud_map = {
            1200: '2',
            2400: '3',
            4800: '4',
            9600: '5',
            19200: '6',
            38400: '7',
            57600: '8',
            115200: '9'
        }
        arg = baud_map.get(baud, '9')
        return self.send_command(self.PROPERTY_BAUD_RATE, arg)

    def change_buzzer_tone(self, tone):
        """
        Change the buzzer frequency between low, med, and high.

        :param tone: int that's 1 = low, 2 = med, 3 = high frequency.
        :return: true if command is successfully sent, false otherwise.
        :rtype: bool
        """
        if 0 < tone < 4:
            return self.send_command(self.PROPERTY_BUZZER_FREQ, str(tone))
        return False

    def enable_decode_beep(self):
        """
        Enable beep on successful read.

        :return: true if command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_DECODE_BEEP, "1")

    def disable_decode_beep(self):
        """
        Disable beep on successful read.

        :return: true if command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_DECODE_BEEP, "0")

    def enable_boot_beep(self):
        """
        Enable beep on module startup.

        :return: true if command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_BOOT_BEEP, "1")

    def disable_boot_beep(self):
        """
        Disable beep on module startup.

        :return: true if command successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_BOOT_BEEP, "0")

    def light_on(self):
        """
        Turn white illumination LED on.

        :return: true if command successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_FLASH_LIGHT, "1")

    def light_off(self):
        """
        Turn white illumination LED off.

        :return: true if command successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_FLASH_LIGHT, "0")

    def reticle_on(self):
        """
        Turn red scan line on.

        :return: true if command successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_AIM_LIGHT, "1")

    def reticle_off(self):
        """
        Turn red scan line off.

        :return: true if command successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_AIM_LIGHT, "0")

    def change_reading_area(self, percent):
        """
        Change the percentage of the frame to scan for barcodes.

        :param percent: Percentage of frame to scan. Valid values are 100, 80, 60, 40, 20.
        :return: true if command successfully sent, false otherwise.
        :rtype: bool
        """
        percent_map = {
            80: '1',
            60: '2',
            40: '3',
            20: '4'
        }
        arg = percent_map.get(percent, '0')
        return self.send_command(self.PROPERTY_READING_AREA, arg)

    def enable_image_flipping(self):
        """
        Enable mirror image reading.

        :return: true if the command successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_MIRROR_FLIP, "1")

    def disable_image_flipping(self):
        """
        Disable mirror image reading.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_MIRROR_FLIP, "0")

    def USB_mode(self, mode):
        """
        Enable USB communication and set the mode.

        :param mode: string defining what USB mode to set the module in. Valid arguments are "KBD", "HID", "232".
        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        if mode in ["KBD", "HID", "232"]:
            return self.send_command(self.PROPERTY_COMM_MODE, mode)
        return False

    def enable_continuous_read(self, repeat_interval=2):
        """
        Enable continuous reading of barcodes and set the time interval for same-code reads.

        :param repeat_interval: int parameter.
            0: same code output 1 times
            1: continuous output with same code without interval
            2: continuous output with same code, 0.5 second interval (default)
            3: continuous output with same code, 1 second interval
        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        if 0 <= repeat_interval < 4:
            self.send_command(self.PROPERTY_READING_MODE, "CNT")
            time.sleep(0.01)
            return self.send_command(self.PROPERTY_CONTINUOUS_MODE_INTERVAL, str(repeat_interval))
        return False

    def enable_motion_sense(self, sensitivity=20):
        """
        Enable the motion sensitive read mode and set sensitivity level.

        :param sensitivity: int value. The smaller the sensitivity, the more sensitive.
            Valid arguments are: 15 (very high), 20 (high/default), 30 (little high), 
            50 (general), 100 (low sensitivity).
        :return: true if command is successfully sent, false otherwise.
        :rtype: bool
        """
        if sensitivity in [15, 20, 30, 50, 100]:
            self.send_command(self.PROPERTY_READING_MODE, "MDH")
            time.sleep(0.01)
            return self.send_command(self.PROPERTY_MOTION_SENSITIVITY, str(sensitivity))
        return False

    def enable_manual_trigger(self):
        """
        Disable the motion sensitive and continuous read mode. Return to the default trigger mode.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_READING_MODE, "MAN")

    def enable_all_1D(self):
        """
        Enable decoding of all 1D symbologies.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_ENABLE_ALL_1D)

    def disable_all_1D(self):
        """
        Disable decoding of all 1D symbologies.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_DISABLE_ALL_1D)

    def enable_all_2D(self):
        """
        Enable decoding of all 2D symbologies.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_ENABLE_ALL_2D)

    def disable_all_2D(self):
        """
        Disable decoding of all 2D symbologies.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.PROPERTY_DISABLE_ALL_2D)

    def start_scan(self):
        """
        Start reading when in trigger mode (default).

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.COMMAND_START_SCAN)

    def stop_scan(self):
        """
        Stop reading when in trigger mode. Module will automatically stop reading after a few seconds.

        :return: true if the command is successfully sent, false otherwise.
        :rtype: bool
        """
        return self.send_command(self.COMMAND_STOP_SCAN)

