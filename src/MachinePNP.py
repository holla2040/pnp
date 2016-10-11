#!/usr/bin/env python
import os, pickle, time
import linuxcnc,math

# references
#   http://linuxcnc.org/docs/2.6/html/common/python-interface.html
# coordinate systems
#    G53   machine
#    G54   camera
#    G55   paste
#    G56   place
#    G57   part tape 0

coordinateInfo = {1:('G54','camera'),2:('G55','paste'),3:('G56','place'),4:('G57','tape')}
enableLabels = ['disabled','enabled']
homeLabels = ['unhomed','homed']

#interpreterStates = {G

# s.estop and s.enabled and s.homed and (s.interp_state

class Machine:
    def __init__(self):
        if os.path.exists("config.machine.p"):
            self.configRecall()
        else:
            self.config = {}
            self.config[''] = 0
            self.configSave()

        self.status = linuxcnc.stat()
        self.command = linuxcnc.command()
        # self.send("G21") # metric
        self.statusTimeout = 0
        self.loopTimeout = 0
        self.vacuum = False

    def home(self,height=20):
        self.send("G0 G90")
        self.send("Z%0.2f"%height)
        self.send("X0 Y0")
        self.send("Z0")

    def homeSet(self):
        self.send("G92 X0 Y0 Z0")

    def mdi(self):
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.wait_complete()

    def manual(self):
        self.command.mode(linuxcnc.MODE_MANUAL)
        self.command.wait_complete()

    def waitForIdle(self):
        while True:
            self.status.poll()
            if self.status.interp_state == linuxcnc.INTERP_IDLE:
                break

    def configSave(self):
        pickle.dump(self.config,open("config.machine.p","wb"))

    def vacuumOn(self):
        self.send("M8")
        self.vacuum = True

    def vacuumOff(self):
        self.send("M9")
        self.vacuum = False

    def vacuumToggle(self):
        if self.vacuum:
            self.vacuumOff()
        else:
            self.vacuumOn()

    def pressureOn(self):
        self.send("M4")

    def pressureOff(self):
        self.send("M3")

    def configRecall(self):
        self.config = pickle.load(open("config.machine.p", "rb" )) 

    def loop(self):
        if time.time() > self.loopTimeout:
            self.status.poll() 
            x = self.status.actual_position[0] - self.status.g5x_offset[0]
            y = self.status.actual_position[1] - self.status.g5x_offset[1]
            t = math.radians(-self.status.rotation_xy)
            self.x = x * math.cos(t) - y * math.sin(t)
            self.y = x * math.sin(t) + y * math.cos(t)
            self.z = self.status.actual_position[2]
            self.loopTimeout  = time.time() + 0.05

    def statusPrintDebug(self):
        for x in dir(self.status):
            if not x.startswith('_'): #and x != "tool_table":
                print x, getattr(self.status,x)
        print

    def statusPrint(self):
        h = self.status.homed
        h = h[0]&h[1]&h[2]&h[3]
        print "x:%-10.3f  y:%-10.3f  z:%-10.3f"%(self.x,self.y,self.z)
        print "%3s %-10s %-8s %-10s"%(coordinateInfo[self.status.g5x_index][0],coordinateInfo[self.status.g5x_index][1],enableLabels[self.status.enabled],homeLabels[h])

    def send(self,c):
        self.command.mdi(c+"\n")
    
if __name__ == "__main__":
    m = Machine()
    while True:
        m.loop()
        if time.time() > m.statusTimeout:
            m.statusPrint()
            m.statusTimeout = time.time() + 2.0;
