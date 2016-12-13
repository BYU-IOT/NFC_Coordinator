#!/usr/bin/env python

import time
from ablib import Pin
import sys
import threading
import uart

nfc_reset = Pin("1", "OUTPUT") #LOW ASSERTED

UART = uart.UART_Control()

class NFC_Control(threading.Thread):

    NFC_RX_size = 30 # Both arrays below have length 24
    NFC_RX = [None]*NFC_RX_size # First 16-bytes are the PAN ID, and second 14 bytes are used in the Encryption key calculation

    #-----NFC COMMANDS-----
    REQB_SENSB = [None]*3
    ATTRIB = [None]*9
    NDEF_APP_SEL = [None]*15
    CAP_CONT_SEL = [None]*9
    CAP_CONT_READ = [None]*7
    NDEF_SEL = [None]*9
    NLEN_READ = [None]*7
    NDEF_READ = [None]*7
    NLEN_CLEAR = [None]*8
    SEND_NDEF = [None]*(12+NFC_RX_size)
    NLEN_UPDATE = [None]*9
    #-----------------------
    TAG_FOUND = 0


    def __init__(self, NFC_send):
        threading.Thread.__init__(self)
        nfc_reset.digitalWrite("LOW") #Reset RFID2 module
        time.sleep(10)
        nfc_reset.digitalWrite("HIGH")
        time.sleep(10)
        self.NFC_RX = NFC_send
        self.initialize_arrays()


    def run(self):
        sys.stderr.write("NFC thread running\n")
        while (True):
            TOTAL_RX = UART.rx(47)
            if "ISO14443 type B: [" in TOTAL_RX:
                self.poll_b(self.NFC_RX)
            if "ISO14443 type A: [" in TOTAL_RX:
                self.poll_a(self.NFC_RX)


    def initialize_arrays(self):
        #-------------------------------REQB/SENSB command---------------------------
        self.REQB_SENSB[0] = 0x05 #(pg.53) of NFC Digital Protocol Tech Spec
        self.REQB_SENSB[1] = 0x00 #(pg.53) AFI - 0x00 selects all application families
        self.REQB_SENSB[2] = 0x00 #(pg.53) PARAM - number of slots...00000100

        #--------------------------------ATTRIB command------------------------------
        self.ATTRIB[0] = 0x1D #start of ATTRIB command
        self.ATTRIB[1] = 0x00 #uint8_ts 2-5 of command select device by it's ID, PUPI
        self.ATTRIB[2] = 0x00
        self.ATTRIB[3] = 0x00
        self.ATTRIB[4] = 0x00
        self.ATTRIB[5] = 0x00 #Param 1 - Should be 0x00
        self.ATTRIB[6] = 0x08 #0x00 #Param 2 - usually 0x08
        self.ATTRIB[7] = 0x05 #0x01 #Param 3 - Listen Mode compliant with ISO/IEC_14443
        self.ATTRIB[8] = 0x00 #Param 4 - pg. 125

        #----------------------------APDU/NDEF Application Select----------------------------------
        self.NDEF_APP_SEL[0] = 0x0A #0x02 #PCB - protocol control uint8_t (ISO 14443-4 Spec), must alternate between commands
        self.NDEF_APP_SEL[1] = 0x00 #CLA - class uint8_t - always 0x00
        self.NDEF_APP_SEL[2] = 0x00
        self.NDEF_APP_SEL[3] = 0xA4 #INS
        self.NDEF_APP_SEL[4] = 0x04 #P1
        self.NDEF_APP_SEL[5] = 0x00 #P2
        self.NDEF_APP_SEL[6] = 0x07 #Lc
        self.NDEF_APP_SEL[7] = 0xD2 #Data uint8_ts...
        self.NDEF_APP_SEL[8] = 0x76
        self.NDEF_APP_SEL[9] = 0x00
        self.NDEF_APP_SEL[10] = 0x00
        self.NDEF_APP_SEL[11] = 0x85
        self.NDEF_APP_SEL[12] = 0x01
        self.NDEF_APP_SEL[13] = 0x01
        self.NDEF_APP_SEL[14] = 0x00 #Le

        #------------------------APDU Capability Container Select-----------------------------
        self.CAP_CONT_SEL[0] = 0x0B #0x03
        self.CAP_CONT_SEL[1] = 0x00 #CLA - class uint8_t
        self.CAP_CONT_SEL[2] = 0x00
        self.CAP_CONT_SEL[3] = 0xA4 #INS
        self.CAP_CONT_SEL[4] = 0x00 #P1
        self.CAP_CONT_SEL[5] = 0x0C #P2
        self.CAP_CONT_SEL[6] = 0x02 #Lc
        self.CAP_CONT_SEL[7] = 0xE1 #Data uint8_ts
        self.CAP_CONT_SEL[8] = 0x03

        #--------------------------Capability Container Read Binary-----------------------------
        self.CAP_CONT_READ[0] = 0x0A #0x02
        self.CAP_CONT_READ[1] = 0x00 #CLA - class uint8_t
        self.CAP_CONT_READ[2] = 0x00
        self.CAP_CONT_READ[3] = 0xB0 #INS
        self.CAP_CONT_READ[4] = 0x00 #P1
        self.CAP_CONT_READ[5] = 0x00 #P2
        self.CAP_CONT_READ[6] = 0x0F #Le

        #------------------------------APDU NDEF Select Procedure-----------------------------
        self.NDEF_SEL[0] = 0x0B #0x03
        self.NDEF_SEL[1] = 0x00
        self.NDEF_SEL[2] = 0x00 #CLA
        self.NDEF_SEL[3] = 0xA4 #INS
        self.NDEF_SEL[4] = 0x00 #P1
        self.NDEF_SEL[5] = 0x0C #P2
        self.NDEF_SEL[6] = 0x02 #Lc
        self.NDEF_SEL[7] = 0xE1 #Data uint8_ts - File ID
        self.NDEF_SEL[8] = 0x04

        #------------------------------Read Binary of NLEN-----------------------------
        self.NLEN_READ[0] = 0x0A
        self.NLEN_READ[1] = 0x00
        self.NLEN_READ[2] = 0x00
        self.NLEN_READ[3] = 0xB0
        self.NLEN_READ[4] = 0x00
        self.NLEN_READ[5] = 0x00
        self.NLEN_READ[6] = 0x02

        #------------------------------APDU NDEF READ Procedure-------------------------------
        self.NDEF_READ[0] = 0x0B
        self.NDEF_READ[1] = 0x00
        self.NDEF_READ[2] = 0x00
        self.NDEF_READ[3] = 0xB0
        self.NDEF_READ[4] = 0x00
        self.NDEF_READ[5] = 0x02
        self.NDEF_READ[6] = 0x00 #Replace this with the NLEN returned

        #------------------------------Clear NLEN field-------------------------------
        self.NLEN_CLEAR[0] = 0x0B
        self.NLEN_CLEAR[1] = 0x00 #################
        self.NLEN_CLEAR[2] = 0x00
        self.NLEN_CLEAR[3] = 0xD6
        self.NLEN_CLEAR[4] = 0x00
        self.NLEN_CLEAR[4] = 0x00
        self.NLEN_CLEAR[5] = 0x02
        self.NLEN_CLEAR[6] = 0x00
        self.NLEN_CLEAR[7] = 0x00

        #--------------------------------Update/send NDEF message---------------------------------------
        self.SEND_NDEF[0] = 0x0A
        self.SEND_NDEF[1] = 0x00 #################
        self.SEND_NDEF[2] = 0x00
        self.SEND_NDEF[3] = 0xD6
        self.SEND_NDEF[4] = 0x00
        self.SEND_NDEF[5] = 0x02
        self.SEND_NDEF[6] = self.NFC_RX_size+5 #,this will change to length of NDEF message + NDEF_BASE
            #---------------START of NDEF format-----------------
        self.SEND_NDEF[7] = 0xD1 #NDEF Header MB=1, ME=1, CF=0, SR=1, IL=0, TNF=001
        self.SEND_NDEF[8] = 0x01 #Type Length 1 uint8_t
        self.SEND_NDEF[9] = self.NFC_RX_size+1 #Payload length
        self.SEND_NDEF[10] = 0x54 #Type T (text)
            #---------------Payload start------------------------
        self.SEND_NDEF[11] = 0x00 #Plain text

        #--------------------------------Update NLEN/NDEF length---------------------------------------
        self.NLEN_UPDATE[0] = 0x0A
        self.NLEN_UPDATE[1] = 0x00
        self.NLEN_UPDATE[2] = 0x00
        self.NLEN_UPDATE[3] = 0xD6
        self.NLEN_UPDATE[4] = 0x00
        self.NLEN_UPDATE[5] = 0x00
        self.NLEN_UPDATE[6] = 0x02
        self.NLEN_UPDATE[7] = 0x00
        self.NLEN_UPDATE[8] = self.NFC_RX_size+5 #length of NDEF, same as SEND_NDEF[6]


    def poll_a(self, NFC_send):
        sys.stderr.write("poll_a\n") #This function sends out a poll with the NFC protocol

        UART.set_protocol_a()
        #=====================================================================================
        #-------------------------------Send REQB/SENSB command---------------------------
        REQA_response = UART.reqa()
        sys.stderr.write("REQA_response: ")
        sys.stderr.write(str(REQA_response))
        sys.stderr.write("\n")

        ID = [0]*5 #variable to store the device's ID
        for i in xrange(5):
            ID[i] = int(REQA_response[(2*i):(2*i)+2], 16)

        WUPA_response = UART.wupa()


        sys.stderr.write("ID: ")
        sys.stderr.write(str(ID))
        sys.stderr.write("\n")
        crc=0
        UART.select_14443a(ID, crc)
        #-----------DONE with WRITE--------------------
        sys.stderr.write("----A TAG WRITTEN----\n")


    def poll_b(self, NFC_send):
        sys.stderr.write("poll_b\n") #This function sends out a poll with the NFC protocol
        UART.set_protocol_b()
        #=====================================================================================
        #-------------------------------Send REQB/SENSB command---------------------------
        REQB_response = UART.reqb()
        sys.stderr.write("Reqb\n")
        PUPI = [None]*4 #variable to store the device's ID
        max_frame_size = 0 #variable to store the max frame size given
        if (REQB_response[0] == 0x50): #, start of REQB/SENSB_RES response-----
            # sys.stderr.write("Found 0x50 response!!!\n")
            for i in range(0,4):
                PUPI[i] = REQB_response[i+1] # #Save devices ID into PUPI variable
            #number_of_app = UART.FIFO[8+extra] #number of applications
            if (REQB_response[9] != 0x00): #
                sys.stderr.write("ERROR!!!!!!! Tag is running > 106kbps\n")
                return
            max_frame_size = int(REQB_response[10]) & 0xF0 # zeros out right 4 bits
            max_frame_size = max_frame_size >> 4
        else:
            sys.stderr.write("NO TAG FOUND!!!\n")
            return
        #=====================================================================================
        #--------------------------------Send ATTRIB command----------------------------------
        UART.attrib(PUPI)
        UART.wait_for_endline(3)
        sys.stderr.write("ATTRIB\n")
        #=====================================================================================
        #----------------------------NDEF Application Select----------------------------------
        UART.request_14443b(self.NDEF_APP_SEL)
        UART.wait_for_endline(2)
        sys.stderr.write("NDEF application select\n")
        #=====================================================================================
        #------------------------Capability Container Select-----------------------------
        UART.request_14443b(self.CAP_CONT_SEL)
        UART.wait_for_endline(2)
        sys.stderr.write("Capability Container\n")
        #=====================================================================================
        #--------------------------Capability Container Read Binary-----------------------------
        UART.request_14443b(self.CAP_CONT_READ)
        UART.wait_for_endline(2)
        sys.stderr.write("Read Capability Container\n")
        #=====================================================================================
        #------------------------------NDEF Select-----------------------------
        UART.request_14443b(self.NDEF_SEL)
        UART.wait_for_endline(2)
        sys.stderr.write("NDEF select\n")
        #=====================================================================================
        #------------------------------NLEN read binary-----------------------------
        UART.flush()
        UART.request_14443b(self.NLEN_READ)
        UART.wait_for_endline(1) #skip 'Request mode'

        sys.stderr.write("Read NLEN:\n")

        z = UART.rx(1)
        while (z != '['):
            z = UART.rx(1)

        rx_array = UART.rx(12)
        NLEN = UART.uart_merge_byte(rx_array[6], rx_array[7])
        self.NDEF_READ[6] = NLEN
        #=====================================================================================
        #------------------------------NDEF read Binary-------------------------------
        UART.request_14443b(self.NDEF_READ)
        UART.wait_for_endline(2)
        #=====================================================================================
        #------------------------------NLEN clear-------------------------------
        UART.request_14443b(self.NLEN_CLEAR)
        UART.wait_for_endline(2)
        sys.stderr.write("NLEN clear\n")
        #=====================================================================================
        #------------------------------Update NDEF message-------------------------------
        # sys.stderr.write(str(NFC_send))
        for i in range(0, self.NFC_RX_size):
            self.SEND_NDEF[i+12] = NFC_send[i]

        UART.request_14443b(self.SEND_NDEF)
        UART.wait_for_endline(2)
        #=====================================================================================
        #------------------------------NLEN Update-------------------------------
        UART.request_14443b(self.NLEN_UPDATE)
        UART.wait_for_endline(2)
        #-----------DONE with WRITE--------------------
        sys.stderr.write("----B TAG WRITTEN----\n")
