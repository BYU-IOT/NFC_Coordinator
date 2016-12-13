#!/usr/bin/env python

import serial
from random import randint
import time
import sys

xbee = serial.Serial(
	port = '/dev/ttyS1',
	baudrate = 115200
)

class XBEE_Control():

	def xbeeCommand(self, command1, command2, value):
		#AT command format
		xbee.write(chr(0x7E))
		xbee.write(chr(0x00))
		xbee.write(chr((4+len(value)) & 0xFF))
		xbee.write(chr(0x08))
		xbee.write(chr(0x00))
		xbee.write(command1)
		xbee.write(command2)
		checksum = 0x08 + ord(command1) + ord(command2)
		for x in range(0, len(value)):
			xbee.write(chr(value[x]))
			checksum += value[x]
		xbee.write(chr(0xFF - (checksum & 0xFF)))

	def write(self, data):
		xbee.write(chr(data))

	def read(self):
		return xbee.read()

	def readline(self):
		return xbee.readline()

	def encrypt(self, key):
		new_key = []
		for i in xrange(15):
			if key[i] < 15:
				new_key.append(key[key[i]])

		while len(new_key) < 16:
			x = len(new_key)-(len(new_key)/2)
			y = len(new_key)-(len(new_key)/3)
			new_key.append(255-((key[x] + key[2] + key[y])/3))

		return new_key

	def split_bytes(self, byte):
		first = byte #write random # as two bytes so Dtag can read
		first &= 0xF0
		first = first >> 4
		if (first < 0xA):
			first += 48
		else:
			first += 55
		second = byte
		second &= 0xF
		if (second < 0xA):
			second += 48
		else:
			second += 55
		return first, second

	def coordinatorSetup(self):
		# The PAN ID has a range of 0x0 - 0xFFFFFFFFFFFFFFFF (8 bytes)
		# The Encryption Key has a range of 0-32 hex characters (16 bytes)
		# The challenge is that writing these credentials to an XBee works differently depending on mode that
		# the XBee is in. Our coordinator is in API mode so we can write the PAN ID and Encryption Key in bytes.
		# So if I want my PAN ID to be 1234, I can write 0x12 then 0x34. But our router/end devices are in AT mode.
		# In AT mode we need to write each nibble as it's own ASCII representation of the character. Using the
		# example above, we'd have to write 0x31, then 0x32, then 0x33, and finally 0x34.
		# This function gets a random number in API mode form, and stores the AT mode version in NFC_send so
		# we can pass it to the router/end device and they don't have to worry about formatting it so the 
		# credentials will match that of the coordinator. We then configure the XBee coordinator with the XBee commands.

		# Because the DLP_RFID2 has the limitation of 30 bytes of data per transaction, and the tag can only receive one transaction
		# before needing to remove from the RF field, we will only send 30 bytes. The first 16 bytes is the Pan ID, 
		# the other 14 bytes is used to create the encryption key.
		PAN_ID = [None]*8
		KEY = [None]*15
		NFC_send = [None]*30
		pos=0
		for i in xrange(8):
			PAN_ID[i] = randint(0,255) #assign random # to temp array
			KEY[i] = PAN_ID[i]
			NFC_send[pos], NFC_send[pos+1] = self.split_bytes(PAN_ID[i])
			pos+=2
		#--------------------------------
		for i in xrange(8,15):
			KEY[i] = randint(0,255) #assign random # to temp array
			NFC_send[pos], NFC_send[pos+1] = self.split_bytes(KEY[i])
			pos+=2

		Encryption_Key = self.encrypt(KEY)

		sys.stderr.write("Encryption_Key:\n")
		for val in Encryption_Key:
			sys.stderr.write(str(hex(val)))
			sys.stderr.write("\n")
		sys.stderr.write("\n")


		sys.stderr.write("KEY:\n")
		for val in KEY:
			sys.stderr.write(str(hex(val)))
			sys.stderr.write(",")
		sys.stderr.write("\n")
		#-----------WRITE PAN ID-------------------
		self.xbeeCommand('I', 'D', PAN_ID)
		time.sleep(.2)
		#-------WRITE ENCRYPTION ENABLE------------------
		self.xbeeCommand('E', 'E', [0x01])
		time.sleep(.2)
		#-------WRITE ENCRYPTION OPTIONS------------------
		self.xbeeCommand('E', 'O', [0x02])
		time.sleep(.2)
		#-------WRITE ENCRYPTION KEY------------------
		self.xbeeCommand('K', 'Y', Encryption_Key)
		time.sleep(.2)
		#-------WRITE NON VOLATILE------------------
		self.xbeeCommand('W', 'R', [0x00])
		
		return NFC_send


