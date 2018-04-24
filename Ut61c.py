#UT61C Measure and parse Class
# author: Michael Auer

import hid
import time

class Ut61c(object):
    def __init__(self):
        super(Ut61c,self).__init__()
        #------------Begin Byte Parse Constants-------------------
        #byte 0 sign
        #byte 1-4 digit
        #byte 5
        #byte 6
        self.komma = {
            0x31: 1000,  #2.000
            0x32: 100,  #20.00
            0x34: 10,  #200.0
            0x30: 1, #2000
        }
        #byte 7
        # Weder Delta noch Norm => MIN/MAX weder AC noch DC %
        # 0:NORM 1:HOLD 2:DELTA 3:AC 4:DC 5:Autorange 6:
        #byte 8 BATT leer? 4
        #byte 9
        self.exp={
            0x00: (1e0,""),
            0x10: (1e6,"M"),
            0x20: (1e3,"k"),
            0x40: (1e-3,"m"),
            0x80: (1e-6,"my"),
            0x02: (1,"%"),
            0x04: (1,""), #Diode
            0x08: (1,"") #durchgang
            }
        #byte 10
        self.mode={
            0x80: "V",
            0x20: u'\u03A9',
            0x08: "Hz",
            0x02: "°C",
            0x01: "°F",
            0x04: "nF",
            0x40: "A",
            0x00: "hmm"
            }
        #------------------End Byte Parse Constants---------------------
        self.msginc=False
        self.msg = []
        self.warningText=("UT61C not found/connected","Choose different Connection in the settings","UT61C USB Connection not established!\nPress and Hold the REL Button until you hear a beep and see the Icon in the upper Left Display of the UT61C")
        self.open=False
        try:
            print("Opening the device")
            self.startTime=time.time()
            self.dev = hid.device()
            self.dev.open(6790,57352) # UT61C VendorID/ProductID
            buf = [0x05,0x60, 0x09, 0x00, 0x60, 0x03] #Start Communication Message
            self.dev.send_feature_report(buf)
            self.open=True
        except IOError as ex:
            print(ex)
            print("UT61C not Connected!")

    def isOpen(self):
        opn=False
        if self.open:
            i=0
            while i<100:
                test=self.measure()
                if test:
                    opn=True
                    i=100
                i+=1
        return opn


    #function to check if bit NR. offset is 1
    def check_bit(self,int_type, offset):
        mask = 1 << offset
        return bool(int_type & mask)

    #function to parse the byteMsg to an readable output
    def parse(self,msg):
        if len(msg)==14:
            if msg[0]==0x2b:
                sign=1
            elif msg[0]==0x2d:
                sign=-1
            else:
                raise UnicodeError("Sign not detected")
            ACDC=""
            if self.check_bit(msg[7],3):
                ACDC="AC"
            elif self.check_bit(msg[7],4):
                ACDC="DC"
            #for a in msg:
            #    print(hex(a),end=", ")
            #print("")
            #print(bin(msg[7]))
            digits=[msg[1]&0x0f,msg[2]&0x0f,msg[3]&0x0f,msg[4]&0x0f]
            digit_value = 0
            for i, digit in zip(range(4), digits):
                digit_value += digit*(10**(3-i))
            display = digit_value / self.komma[msg[6]]
            display_value = display * self.exp[msg[9]][0]
            #print(str(display)+ " " + self.exp[msg[9]][1] + self.mode[msg[10]] + " " + ACDC)
            #print(display_value)
            return (display_value,self.mode[msg[10]])
        else:
            raise UnicodeError("Message to short")


    #function to read 2 Bytes from the USB Connection
    def measure(self):
        try:
            byteMsg = bytes(self.dev.read(2))
        except OSError:
            self.open=False
            return None
        if byteMsg:
            if byteMsg[0]==0xf1: #0xf1 maybe "successfull measurment"?
                self.msg.append(byteMsg[1])
                self.msginc=True
                return False
            else:
                data=False
                if (self.msginc):
                    try:
                        par=self.parse(self.msg)
                        t=time.time()-self.startTime
                        data=(t,par[0],("Zeit","s"),("Wert",par[1]))
                    except UnicodeError as ex:
                        print(ex)
                self.msg=[]
                self.msginc=False
                return data
        else:
            return False
