#!/usr/bin/env python

import argparse
import threading
import os
import requests
from websocket import create_connection
import sys
import pickle
import time
import os.path
from ablib import Pin
import xbee
from nfc import NFC_Control
from sound import Volume_Control
from sound import Doorbell_Control
from network import ServerToXbeeThread
from network import XbeeToServerThread

XBEE = xbee.XBEE_Control()

class Coordinator:
	NFC_send = [None]*30 #48 #Initialize the array that will hold the XBee Pan ID, and Encryption Key

	def __init__(self):
		self.parse_arguments()

	def parse_arguments(self):
		'''
		parser = argparse.ArgumentParser(prog='Coordinator device', description = 'The coordinating device')
		parser.add_argument('-d', '--debug', action='store_true', help='turn on debug mode', default=False)
		args = parser.parse_args()
		self.debug = args.debug
		'''

	def run(self):
		#Check if there are previous settings for the XBee Coordinator. If not, set it up
		if (os.path.exists("usr/local/coordinator/settings.pickle")):
			self.NFC_send = pickle.load(open("usr/local/coordinator/settings.pickle", "rb"))
		else:
			self.NFC_send = XBEE.coordinatorSetup()
			pickle.dump(self.NFC_send, open("usr/local/coordinator/settings.pickle", "wb"))
		# Create threads
		self.createThreads()

	def createThreads(self):
		# create threads
		threads = []
		threads.append(NFC_Control(self.NFC_send))
		threads.append(ServerToXbeeThread(ws))
		threads.append(XbeeToServerThread(ws))
		#threads.append(Volume_Control())
		#threads.append(Doorbell_Control())
		# run threads
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		sys.stderr.write("Should not get here")

	def endThreads(self):
		for t in threads:
			t.stop()


if __name__ == "__main__":
	try:
		c = Coordinator()
		ws = create_connection("ws://23.253.50.248:3000/webSS") 
		c.run()
	except (IOError, KeyboardInterrupt), e:
		sys.stderr.write("Error: exception Coordinator.py\n")
		sys.stderr.write(str(e))
		sys.stderr.write("\n")

