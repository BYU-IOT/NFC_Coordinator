#!/usr/bin/env python

import sys
import xbee
import threading

XBEE = xbee.XBEE_Control()

class ServerToXbeeThread(threading.Thread):
	def __init__(self, websocket):
		threading.Thread.__init__(self)
		self.ws = websocket

	def run(self):
		sys.stderr.write("Server to Xbee Thread\n")
		while (True):
			# Wait for something from the server
			result = self.ws.recv()
			# print "Received: {}".format(result)
			# send result to the xbee
			if result != ".......":
				result = result[:-1]
				for r in result.split(','):
					XBEE.write(chr(int(r)))


class XbeeToServerThread(threading.Thread):
	def __init__(self, websocket):
		threading.Thread.__init__(self)
		self.ws = websocket

	def run(self):
		# Connect to the server
		# Upgrade to websockets
		sys.stderr.write("Xbee to Server Thread\n")

		MSB_length = 0
		LSB_length = 0 # These have to be here because if not python thinks these variables are not initialized and throws errors.
		while (True):
			x = XBEE.read()
			while (format(ord(x),"x") != "7e"): #wait til we find a start byte
				x = XBEE.read()

			MSB_length = format(ord(XBEE.read()),"x")
			LSB_length = format(ord(XBEE.read()),"x")

			length = (int(MSB_length, 16) << 4) | int(LSB_length, 16)

			message = "7e," + MSB_length + "," + LSB_length + ","
			for i in range(0, length+1):
				message += "{},".format(format(ord(XBEE.read()),"x"))
			# Send it to the server
			self.ws.send(message)