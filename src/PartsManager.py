#!/usr/bin/env python
try:
    import BeautifulSoup
except:
    import bs4 as BeautifulSoup
import os, pickle

class PartsManager:
    def __init__(self,fn):
        if os.path.exists("data.parts.p"):
            self.partsRecall()
        else:
            fnt = open(fn).read()
            try:
                self.soup = BeautifulSoup.BeautifulSoup(fnt,"lxml")
            except:
                self.soup = BeautifulSoup.BeautifulSoup(fnt)
            
            self.packages = {}
            self.parts = {}
            self.pads = {}

            self.packagesGet()
            self.padsGet()
            self.partsGet()

            self.partsRemove()

        self.valuesGet()
        self.partsSave()

    def partsSave(self):
        pickle.dump(self.parts,open("data.parts.p","wb"))

    def partsRecall(self):
        self.parts = pickle.load(open("data.parts.p", "rb" )) 

    def partDelete(self, name):
        try:
            del self.parts[name]
            self.partsSave()
            self.valuesGet()
        except:
            print name,"not found"

    def valuesGet(self):
        self.values = {}
        for name in self.parts.keys():
            part = self.parts[name]
            value = part['value']
            if not self.values.has_key(value):
                self.values[value] = []
            self.values[value].append(name)
            self.values[value].sort()
            
    def statusPrint(self):
        for value in self.values.keys():
            vals = ",".join(self.values[value][0:15])
            if len(self.values[value]) > 15:
                vals += ",..."
            print "%-10s %-2d %s"%(value[0:9],len(self.values[value]),vals)

    def partsRemove(self):
        for name in self.parts.keys():
            if (len(self.parts[name]['pads']) < 1) or (self.parts[name]['value'] == "DNP"):
                del self.parts[name]

    def packagesGet(self):
        for package in self.soup.findAll("package"):
            name = package['name']
            self.packages[name] = {'name':name,'pads':{}}
            for smd in package.findAll("smd"):
                self.packages[name]['pads'][smd['name']] = {}
                self.packages[name]['pads'][smd['name']]['x'] = float(smd['x'])
                self.packages[name]['pads'][smd['name']]['y'] = float(smd['y'])

    def partsGet(self):
        for element in self.soup.findAll("element"):
            name = element['name']
            value = element['value']
            x = float(element['x'])
            y = float(element['y'])
            p = element['package']

            try:
                rotation = int(element['rot'][1:])
            except:
                rotation = 0

            self.parts[name] = {'name':name,'x':x,'y':y,'value':value,'rotation':rotation,'package':p,'placed':False,'pads':self.pads[name]}

    def padsGet(self):
        for element in self.soup.findAll("element"):
            name = element['name']
            value = element['value']
            package = self.packages[element['package']]
            self.pads[name] = []
            for pad in package['pads'].keys():
                x = float(element['x'])
                y = float(element['y'])
                try:
                    rotation = int(element['rot'][1:])
                except:
                    rotation = 0

                # print name,x,y,rotation,package['pads'][pad]
                if rotation == 0:
                    y += round(float(package['pads'][pad]['y']),3)
                    x += round(float(package['pads'][pad]['x']),3)
                else:
                    if rotation == 180:
                        y -= round(float(package['pads'][pad]['y']),3)
                        x -= round(float(package['pads'][pad]['x']),3)
                    else:
                        if rotation == 90:
                            x -= round(float(package['pads'][pad]['y']),3)
                            y += round(float(package['pads'][pad]['x']),3)
                        else:
                            x += round(float(package['pads'][pad]['y']),3)
                            y -= round(float(package['pads'][pad]['x']),3)
                self.pads[name].append([x,y])

if __name__ == "__main__":
    os.system("rm -f data.parts.p")
    p = PartsManager('a.brd')
    p.statusPrint()
