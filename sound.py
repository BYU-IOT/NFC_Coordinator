#!/usr/bin/env python

import sys
import subprocess
import time
import threading
from ablib import Pin

#Pin 2 can't be used.
#Pin 3 is the potentiometer. It will be accessed by a different function for ADC
push_button = Pin("4", "INPUT")

LED = Pin("12", "OUTPUT")

########################################################################################################

class Volume_Control(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		previous_value = 0
		while True:
			current_value = self.get_pot_value()
			if (previous_value != current_value):
				previous_value = current_value
				self.set_volume(self.pot_convert(current_value))
			LED.digitalWrite("LOW")
			time.sleep(.5)
			LED.digitalWrite("HIGH")
			time.sleep(.5)

	def pot_convert(self, pot_value):
		switch = {
			895 : "0",
			927 : "0",
			943 : "10",
			951 : "20",
			955 : "30",
			959 : "40",
			991 : "50",
			1007 : "60",
			1015 : "70",
			1019 : "80",
			1021 : "90",
			1022 : "90",
			1023 : "100",
		}
		return switch.get(pot_value, "100")

	def get_pot_value(self):
		P = subprocess.Popen('cat /sys/bus/iio/devices/iio\:device0/in_voltage2_raw', shell=True, stdout=subprocess.PIPE)
		return int(P.stdout.read())

	def set_volume(self, volume):
		volume += "%"
		subprocess.call(["amixer", "sset", "\"PCM\"", volume])

########################################################################################################

class Doorbell_Control(threading.Thread):
	ringtone = "/usr/local/coordinator/doorbell_tone.wav"

	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		while True:
			if (push_button.digitalRead() is 0):
				self.play_tone(self.ringtone)
			time.sleep(.2)

	def play_tone(self, tone):
		subprocess.Popen(["aplay", "-D", "iec958:CARD=CODEC,DEV=0", tone])
		