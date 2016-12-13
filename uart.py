#!/usr/bin/env python

import serial
import sys
import time
import subprocess
from ablib import Pin

nfc = serial.Serial(
    port = '/dev/ttyS2',
    baudrate = 115200,
    timeout = None,
    bytesize = serial.EIGHTBITS, #number of bits per byte
	parity = serial.PARITY_NONE, #set parity check: no parity
	stopbits = serial.STOPBITS_ONE #number of stop
)

class UART_Control():
	def __init__(self):
		try:
			nfc.close()
			nfc.open()
		except Exception, e:
			sys.stderr.write("UART INIT OPEN ERROR\n")
			sys.stderr.write(str(e))
			sys.stderr.write("\n\n")
			exit()
		if (nfc.isOpen()):
			try:
				nfc.flushInput()
				nfc.flushOutput()
			except Exception, e:
				sys.stderr.write(str(e))

	def uart_split_byte(self, byte):
		# The RFID2 needs to receive each byte as two ASCII representations of the upper and lower nibbles.
		# For example if we want to send 0x12, we have to send 0x31, then 0x32. This function takes a byte
		# and splits it as so and returns it as a two byte buffer.
		buf = [None]*2
		buf[1] = 0x0F & byte #lower nibble
		buf[0] = (byte >> 4) & 0x0F #upper nibble
		if (buf[0] < 0x0A):
			buf[0] += 48
		else:
			buf[0] += 55

		if (buf[1] < 0x0A):
			buf[1] += 48
		else:
			buf[1] += 55
		return buf

	def uart_merge_byte(self, byte_high, byte_low):
		# The RFID2 sends data back as ASCII characters. This function takes two ASCII characters
		# (the upper and lower nibbles) and merges them into one hex byte for further computation.
		nibbles = [None]*2
		nibbles[0] = byte_high
		nibbles[1] = byte_low
		regValue = ''.join(nibbles)
		return int(regValue, 16)

	def read_register(self, address):
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0A))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x12))
		tx_array.extend(self.uart_split_byte(address))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		return nfc.read(36)

	def write_register(self, address, value):
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0A))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(address))
		tx_array.extend(self.uart_split_byte(value))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)

	def set_protocol_a(self): #This just sets the main register's values for 14443A communication.
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0A))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x21)) #0x88
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		self.wait_for_endline(1)

		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x21))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x09))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		self.wait_for_endline(1)

		tx_array = [] #AGC Toggle
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x09))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0xF0))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		self.wait_for_endline(1)

		tx_array = [] #AM PM Toggle
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x09))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0xF1))
		tx_array.extend(self.uart_split_byte(0xFF))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		self.wait_for_endline(1)

	def set_protocol_b(self):
		#This just sets the main register's values for 14443B communication.
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0A))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)

		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x21))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		self.wait_for_endline(4)

	def reset_RF(self):
		tx_array = [] #turn off RF field
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)

		tx_array = [] #turn back on the RF field
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x10))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x21))
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0C))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)

	def wait_for_endline(self, num):
		# The RFID2 responds with every request with a "\r\n" first, the data, then another "\r\n"
		# This function just waits for the endlines to make sure the RFID2 is responding. We'll timeout if
		# something goes wrong. num is the number of endlines to wait for.
		for i in range(0, num):
			start = time.time()
			check = nfc.read()
			count = 0
			while(1):
				if (check == "\n"):
					break
				if ((time.time() - start) > (1.1)):
					break
				check = nfc.read()

	def reqa(self):
		#14443A REQA
		nfc.flushInput()
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x09))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0xA0))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		sys.stderr.write("REQA sent\n")
		z = nfc.read()
		while (z != '['):
			z = nfc.read()
		rx_array = nfc.read(10)
		return rx_array

	def wupa(self):
		#14443A WUPA
		nfc.flushInput()
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x09))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0xA1))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		sys.stderr.write("WUPA sent\n")
		# z = nfc.read()
		# while (z != '['):
		# 	z = nfc.read()
		# rx_array = nfc.read(10)
		# return rx_array

	def reqb(self):
		#########REQUEST PUPI################
		#14443B REQB
		nfc.flushInput()
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x09))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0xB0))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		z = nfc.read()
		while (z != '['):
			z = nfc.read()
		rx_array = nfc.read(30)
		RX = [0]*12
		for i in range(0, 12):
			RX[i] = self.uart_merge_byte(rx_array[(2*i)], rx_array[(2*i)+1])
		return RX

	def select_14443a(self, ID, crc):
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x0D))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0xA2))
		tx_array.extend(self.uart_split_byte(int(ID[0]))) #select ID
		tx_array.extend(self.uart_split_byte(int(ID[1])))
		tx_array.extend(self.uart_split_byte(int(ID[2])))
		tx_array.extend(self.uart_split_byte(int(ID[3])))
		tx_array.extend(self.uart_split_byte(int(ID[4])))
		tx_array.extend(self.uart_split_byte(crc))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)
		self.wait_for_endline(1)

	def attrib(self, pupi):
		#########ATTRIB################
		#Request mode
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(0x11))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x18))
		tx_array.extend(self.uart_split_byte(0x1D))
		tx_array.extend(self.uart_split_byte(pupi[0])) #PUPI
		tx_array.extend(self.uart_split_byte(pupi[1]))
		tx_array.extend(self.uart_split_byte(pupi[2]))
		tx_array.extend(self.uart_split_byte(pupi[3]))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x08))
		tx_array.extend(self.uart_split_byte(0x05))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)

	def request_14443b(self, request):
		req_len = len(request)
		tx_array = []
		tx_array.extend(self.uart_split_byte(0x01))
		tx_array.extend(self.uart_split_byte(8+req_len))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x03))
		tx_array.extend(self.uart_split_byte(0x04))
		tx_array.extend(self.uart_split_byte(0x18))
		for i in range(0, req_len):
			tx_array.extend(self.uart_split_byte(request[i]))
		tx_array.extend(self.uart_split_byte(0x00))
		tx_array.extend(self.uart_split_byte(0x00))
		nfc.write(tx_array)

	def flush(self):
		nfc.flushInput()

	def rx(self, num):
		return nfc.read(num)



