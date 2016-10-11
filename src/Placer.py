#!/usr/bin/env python
from PartsManager import PartsManager
from MachinePNP import Machine
from getchar import getchar
import time, os, pickle, sys, math

# coordinate systems
#    G53   machine
#    G54   camera
#    G55   paste
#    G56   place
#    G57   part tape 0

try:
    import BeautifulSoup
except:
    import bs4 as BeautifulSoup

class Placer:
    def __init__(self,brd):
        self.pm = PartsManager(brd)
        self.m  = Machine()
        self.statusTimeout = 0
        self.pmTimeout = 0
        self.running = True
        self.screenClear()

        if os.path.exists("config.placer.p"):
            self.configRecall()
        else:
            self.config = {}
            self.config['partHeightMax'] = 10.0
            self.config['placedPartHeight'] = 0.5
            self.config['statusInterval'] = 0.25
            self.config['pmInterval'] = 5.0
            self.config['solderMoveInPartHeight'] = 3.0
            self.config['tapeOffset'] = 4.0
            self.config['tapeCount'] = 0
            self.config['handPlaceLocation'] = (140,50)
            self.config['jogHeight'] = 13.0

            fnt = open(brd).read()
            try:
                self.soup = BeautifulSoup.BeautifulSoup(fnt,"lxml")
            except:
                self.soup = BeautifulSoup.BeautifulSoup(fnt)
            self.dimensionFind()

            self.configSave()

        self.screenClear()

    def partList(self):
        self.screenPos(1,1)
        self.screenClear('eol')
        ans = raw_input("part? ")
        list = []
        if ans:
            if self.pm.values.has_key(ans):
                list = self.pm.values[ans]
            else:
                ans = ans.upper() # its a part
                if self.pm.parts.has_key(ans):
                    list = [ans]      # user gave us a part name, not a value
        self.screenPos(1,3)
        self.screenClear('eol')
        return list

    def dimensionFind(self):
        xmax = 0
        ymax = 0
        for wire in self.soup.findAll('wire',{'layer':'20'}):
            x = int(wire['x1'])
            if x > xmax:
                xmax = x
            y = int(wire['y1'])
            if y > ymax:
                ymax = y
        self.config['xmax'] = xmax
        self.config['ymax'] = ymax

    def machineStatus(self):
        self.screenPos(1,5)
        print "Machine"
        self.m.statusPrint()

    def partsStatus(self):
        self.screenPos(1,9)
        self.screenClear('eos')
        print "Parts"
        self.pm.statusPrint()

    def loop(self):
        self.m.loop()
        c = getchar()
        if c:
            self.handler(c)
        if time.time() > self.statusTimeout:
            self.machineStatus()
            self.statusTimeout = time.time() + self.config['statusInterval'];
        if time.time() > self.pmTimeout:
            self.partsStatus()
            self.pmTimeout = time.time() + self.config['pmInterval'];

    def configSave(self):
        pickle.dump(self.config,open("config.placer.p","wb"))

    def configRecall(self):
        self.config = pickle.load(open("config.placer.p", "rb" )) 

    def info(self):
        self.pm.info()
        self.m.info()

    def screenClear(self,what='screen'):
            '''
            erase functions:
                    what: screen => erase screen and go home
                          line   => erase line and go to start of line
                          bos    => erase to begin of screen
                          eos    => erase to end of screen
                          bol    => erase to begin of line
                          eol    => erase to end of line
            '''
            clear = {
                    'screen': '\x1b[2J\x1b[H',
                    'line': '\x1b[2K\x1b[G',
                    'bos': '\x1b[1J',
                    'eos': '\x1b[J',
                    'bol': '\x1b[1K',
                    'eol': '\x1b[K',
                    }
            sys.stdout.write(clear[what])
            sys.stdout.flush()

    def screenPos(self,x,y):
        sys.stdout.write('\x1b[%d;%dH'%(y,x))
        sys.stdout.flush()

    def setup(self):
        self.m.send("G0 G90")
        for i in range(5):
            self.m.send("X0Y0")
            #self.m.send("G4P1")
            self.m.send("X%dY%d"%(self.config['xmax'],self.config['ymax']))
            #self.m.send("G4P1")
            self.m.send("X%dY0"%self.config['xmax'])
            #self.m.send("G4P1")
            self.m.send("X0Y%d"%self.config['ymax'])
            #self.m.send("G4P1")
            #self.m.send("X0Y0")
            #self.m.send("G4P1")
        self.m.send("X0Y0")

    def handler(self,c):
        if c == "q":
           self.running = False
        '''
        if c == "i":
            self.m.send("G0 G91 Y0.1")
        if c == "k":
            self.m.send("G0 G91 Y-0.1")
        if c == "j":
            self.m.send("G0 G91 X-0.1")
        if c == "l":
            self.m.send("G0 G91 X0.1")
        if c == "I":
            self.m.send("G0 G91 Y1.0")
        if c == "K":
            self.m.send("G0 G91 Y-1.0")
        if c == "J":
            self.m.send("G0 G91 X-1.0")
        if c == "L":
            self.m.send("G0 G91 X1.0")
        if c == "d":
            self.m.send("G0 G91 Z-0.1")
        if c == "e":
            self.m.send("G0 G91 Z0.1")
        if c == "D":
            self.m.send("G0 G91 Z-1.0")
        if c == "E":
            self.m.send("G0 G91 Z1.0")
        '''
        if c == "E":
            self.m.send("G0 G91 Z1.0")
        if c == "H":
            self.home()
        if c == "?":
            self.screenClear()
        if c == "g":
            self.partInspect()
        if c == "s":
            self.partSolder()
        if c == "p":
            self.partPlace()
        if c == "v":
            self.m.vacuumToggle()
        if c == "R":
            self.partRemove()
        if c == "X":
            self.setup()
        if c == "C":
            self.calibate()

    def calibate(self):
        xlen = 188.00
        ylen = 88.00
        cal = 36.576
        self.screenPos(1,1)
        self.screenClear('line')
        ans = raw_input("calibrate x,y? ")
        if ans:
            x,y = ans.split(',')
            x = (xlen/float(x))*cal
            y = (ylen/float(y))*cal
            print "x %.8f\ny %.8f"%(x,y)

    def partSolder(self):
        list = self.partList()
        if list:
            self.m.mdi()
            tempParts = []
            for pname in list:
                tempParts.append(self.pm.parts[pname])
            partCur = {'x':self.m.x,'y':self.m.y}
            partGroup = []
            partNearest = None
            while len(tempParts):
                dmin = 10000
                for p in tempParts:
                    d = math.sqrt(math.pow(partCur['x']-p['x'],2) + math.pow(partCur['y']-p['y'],2))
                    if d < dmin:
                        partNearest = p
                        dmin = d
                partGroup.append(partNearest)
                tempParts.remove(partNearest)
                partCur = partNearest

            self.m.send("G0 G90")
            for part in partGroup:
                pads = part['pads']
                #self.m.send("G0 G90 Z%-0.4f"%(self.m.config['solderzoffset']+self.config['partHeightMax']))
                for pad in pads:
                    x,y = pad
                    self.screenPos(1,1)
                    self.screenClear('eol')
                    print "solder paste for %4s at %0.2f,%0.2f"%(part['name'],x,y)

                    self.m.send("X%0.4f Y%0.4f"%(x,y))
                    self.m.pressureOn()
                    #self.m.send("G0 G90 Z%-0.4f"%self.m.config['solderzoffset'])
                    self.m.send("G4 P0.1") # dwell
                    self.m.pressureOff()
                    #self.m.send("G0 G90 Z%-0.4f"%(self.m.config['solderzoffset']+self.config['solderMoveInPartHeight']))
                    time.sleep(2)

        #self.m.send("G0 G90 Z%0.2f"%self.config['partHeightMax'])
        #self.screenPos(1,3)
        #self.screenClear('eos')
        self.pmTimeout = 0 # forces refresh

    def partRemove(self):
        self.screenPos(1,3)
        ans = raw_input("remove part? ")
        if len(ans):
            self.pm.partDelete(ans)
        self.screenPos(1,3)
        self.screenClear('eos')
        self.pmTimeout = 0 # forces refresh

    def partPlace(self):
        list = self.partList()
        if list:
            self.m.mdi()
            self.config['tapeCount'] = 0
            self.configSave()
            self.m.send("G0 G90")
            for pname in list:
                self.screenPos(1,1)
                self.screenClear('eol')
                part = self.pm.parts[pname]
                x = part['x']
                y = part['y']
                r = part['rotation']

                print "placing %4s at %0.2f,%0.2f@%0.1f"%(pname,x,y,r)

                #self.m.send("Z%0.2f"%self.config['partHeightMax'])
                self.m.send("G57 X%0.4f Y0.00"%(self.config['tapeCount']*self.config['tapeOffset']))
                #self.m.send("Z%0.4f"%self.m.config['pv0zoffset'])
                self.m.vacuumOn();
                self.m.send("G4 P1.0") #dwell
                #self.m.send("Z%0.2f"%self.config['partHeightMax'])
                self.m.send("G54 X%0.4f Y%0.4f"%(x,y))
                self.config['tapeCount'] += 1
                self.configSave()
                #self.m.send("G0 G90 Z%0.2f"%self.config['placedPartHeight'])
                self.m.vacuumOff();
                self.m.send("G4 P1.0")
                #self.m.send("G0 G90 Z%0.2f"%self.config['partHeightMax'])
                self.m.waitForIdle()
                self.pm.partDelete(pname)
                self.pmInfo()
        #self.m.send("G0 G90 Z%0.2f"%self.config['partHeightMax'])
        self.pmTimeout = 0 # forces refresh

    def partInspect(self):
        list = self.partList()
        if list:
            self.m.mdi()
            for pname in list:
                self.screenPos(1,1)
                self.screenClear('eol')
                print "inspect %s"%pname
                self.m.send("G54 G0 G90"); # pick camera coordinate
                self.m.send("Z%0.2f"%self.config['jogHeight']) #move to safe height 
                part = self.pm.parts[pname]
                self.m.send("X%0.2f Y%0.2f"%(part['x'],part['y']))
                self.m.send("G4 P1.5") #dwell

    def offsetSet(self):
        self.screenPos(1,3)
        ans = raw_input("SET offset H,v,h,s,m? ")
        if ans == 'v':
            self.m.pv0OffsetSet()
        if ans == 'h':
            self.m.ph0OffsetSet()
        if ans == 's':
            self.m.solderOffsetSet()
        if ans == 'H':
            self.m.homeSet()
        if ans == 'm':
            self.m.manualOffsetSet()
        self.screenPos(1,3)
        self.screenClear('line')

    def go(self):
        self.screenPos(1,3)
        ans = raw_input("go offset H,v,h,s,p,m,M? ")
        if ans == 'v':
            self.m.pv0OffsetGo(self.config['partHeightMax'])
        if ans == 'h':
            self.m.ph0OffsetGo(self.config['partHeightMax'])
        if ans == 's':
            self.screenPos(1,3)
            ans = raw_input("place tool removed y? ")
            if ans == "y":
                self.m.solderOffsetGo(self.config['partHeightMax'])
        if ans == 'H':
            self.m.homeGo()
        if ans == 'p':
            self.m.send("G0 G90 Z%0.2f"%self.config['partHeightMax'])
            self.m.send("G0 G90 X%0.2f Y%0.2f"%self.config['handPlaceLocation'])
        if ans == 'm':
            self.m.manualOffsetGo(self.config['partHeightMax'])
        if ans == 'M':
            self.moveToPart()
        self.screenPos(1,3)
        self.screenClear('line')

    def home(self):
        self.m.manual()
        while True:
            self.screenPos(1,1)
            self.screenClear('line')
            ans = raw_input("home x,y,z,a? ")
            if ans:
                if ans == 'x':
                    self.m.command.home(0)
                if ans == 'y':
                    self.m.command.home(1)
                if ans == 'z':
                    self.m.command.home(2)
                if ans == 'a':
                    self.m.command.home(3)
            else:
                break
        self.screenPos(1,1)
        self.screenClear('line')


if __name__ == "__main__":
    #os.system("rm -f config.placer.p")
    p = Placer('a.brd')
    while p.running:
        p.loop()

