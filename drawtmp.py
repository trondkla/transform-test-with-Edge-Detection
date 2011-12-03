#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from functools import partial
from itertools import permutations
from PySide import QtCore, QtGui
from PySide.QtCore import QPointF, QRectF, QLineF
from PySide.QtGui import QTransform, QColor, QVector2D
import json
import atexit
has_midi = False
try:
    import pypm
    has_midi = True
except:
    pass

class floatn:
    def __init__(self, *args):
        if(len(args)==0):
            self.values = [0.0]*4
        else:
            self.values = list(args)
        
        for val in list(permutations('xyzw'))+['x','y','z','w']:
            setattr(self, ''.join(val), partial(self.__getitem__, ''.join(val)))
            
    def lookupIdx(self, id):
        return [ord(c)-ord('x') for c in id]

    def __getitem__(self, idx):
        if isinstance(idx, (int, long)):
            return self.values[idx]
        else:
            ret =  [self.values[i] for i in self.lookupIdx(idx)]
            if len(idx) == 1:
                return ret[0]
            else:
                return ret

    def __setitem__(self, idx, val):
        if isinstance(idx, (int, long)):
            self.value[idx] = val
        else:
            if isinstance(val, (QVector2D)):
                val = [val.x(), val.y()]
            if isinstance(val, (int)):
                val = val*1.0
            if isinstance(val, (float)):
                val = [val]
            for idx, clsIdx in enumerate(self.lookupIdx(idx)):
                self.values[clsIdx] =  val[idx]
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ','.join([str(v) for v in self.values]))

class float2(floatn):
    pass

class float4(floatn):
    pass

def find_points(ppoi, eye):
    retpt = float4(0.0,0.0,0.0,0.0)
    scale = -1.0*ppoi['y']/eye['y'];
    scaleinner = 0.0
    retpt['x'] = ppoi['x']+(eye['x']*scale); #if at first cube plane
    print retpt['x']
    if (0.0 < retpt['x'] and retpt['x'] < 1.0):
        retpt['y'] = 0.0; # (DEFINED) 
    elif (retpt['x'] > 1.0):#below
        if(eye['x']>0.0):#Eye goes down
            retpt['y'] = 0.0#float('nan');
        else:#Eye goes up
            retpt['y'] =  ((1.0-retpt['x'])*eye['y'])/eye['x']
            print "EyeY:", retpt['y'] 
            retpt['x'] = 1.0
            if retpt['y'] > 1.0:
                retpt['y'] = 0.0 # NAN
                return float4(0.0,0.0,0.0,0.0)
    elif (retpt['x'] < 0.0):#over
        if(eye['x']<0.0):#Eye goes up
            retpt['y'] = 0.0#float('nan');
        else:#Eye goes up
            retpt['y'] =  ((-1.0*retpt['x'])*eye['y'])/eye['x']
            print "EyeY:", retpt['y'] 
            retpt['x'] = 0.0
            if retpt['y'] > 1.0:
                retpt['y'] = 0.0 # NAN
                return float4(0.0,0.0,0.0,0.0)
    scaleinner = (1.0-retpt['y'])/eye['y'];
    retpt['z'] = retpt['x'] + eye['x'] * scaleinner;#antar at dybden på kuben alltid er 1
    retpt['w'] = retpt['y'] + eye['y'] * scaleinner;
    if (0.0 < retpt['z'] and retpt['z'] < 1.0):
        retpt['w'] = 1.0; # (DEFINED) 
    elif (retpt['z'] > 1.0):#below
        if(eye['x']>0.0):#Eye goes down
            retpt['w'] = 0.0#float('nan');
        else:#Eye goes up
            retpt['w'] =  ((1.0-retpt['z'])*eye['y'])/eye['x']
            print "EyeY:", retpt['w'] 
            retpt['z'] = 1.0
    elif (retpt['z'] < 0.0):#over
        if(eye['x']<0.0):#Eye goes up
            retpt['w'] = 0.0#float('nan');
        else:#Eye goes up
            retpt['w'] =  ((-1.0*retpt['z'])*eye['y'])/eye['x']
            print "EyeY:", retpt['w'] 
            retpt['z'] = 0.0
    if retpt['w'] > 1.0:
        retpt['w'] = 0.0 # NAN
        return float4(0.0,0.0,0.0,0.0)
    return retpt;


class Example(QtGui.QWidget):
    
    def __init__(self):
        global has_midi
        self.mrotation = 0
        self.mtranslate = QPointF(0.0,0.0)
        self.mscale = QPointF(1.0,1.0)
        self.dof = -2.0
        self.epx = 0.5
        self.ppx = 0.6
        self.ppy = 0.0

        self.loadFile()
        super(Example, self).__init__()
        if has_midi:
            self.midi = pypm.Input(0)
            self.timer = QtCore.QTimer(self);
            self.timer.timeout.connect(self.timerEvent)
            self.timer.start(100)
        self.initUI()

    def loadFile(self):
        try:
            json_data=open('json_data.txt')
            variables = json.load(json_data)
            json_data.close()

            self.mrotation = variables['mrotation']
            self.mtranslate.setX(variables['mtranslatex'])
            self.mtranslate.setY(variables['mtranslatey'])
            self.mscale.setX(variables['mscalex'])
            self.mscale.setY(variables['mscaley'])
            self.dof = variables['dof']
            self.epx = variables['epx']
            self.ppx = variables['ppx']
            self.ppy = variables['ppy']

        except:
            print "Could not load file"
    
    def saveFile(self):
        data = {}
        data['mrotation'] = self.mrotation
        data['mtranslatex'] = self.mtranslate.x()
        data['mtranslatey'] = self.mtranslate.y()
        data['mscalex'] = self.mscale.x()
        data['mscaley'] = self.mscale.y()
        data['dof'] = self.dof
        data['epx'] = self.epx
        data['ppx'] = self.ppx
        data['ppy'] = self.ppy
          
        try:
            json_data=open('json_data.txt', 'w')
            json_data.write(json.dumps(data))
            json_data.close()
        except:
            print "Could not save file"
        
    def initUI(self):      

        self.setGeometry(300, 300, 500, 500)
        self.setWindowTitle('Transform test')
        self.show()


    def timerEvent(self):
        gotpkg = False
        while True:
            pkg = self.midi.Read(1) 
            if pkg:
                gotpkg = True
                data, counter = pkg[0]
                bank, instrument, value, val2 = data
                if instrument==2:
                    self.mrotation = int(value*2.83)
                if instrument==3:
                    self.mscale.setX(value/75.0)
                    if(self.mscale.x()==0.0):
                        self.mscale.setX(0.001)
                if instrument==4:
                    self.mscale.setY((value/127.0)**1.25)
                    if(self.mscale.y()==0.0):
                        self.mscale.setY(0.001)
                if instrument==15:
                    self.mtranslate.setX((value/32.0)-2.0)
                if instrument==16:
                    self.mtranslate.setY((value/32.0)-2.0)
                if instrument==5:
                    self.epx = (value/20.0)-1.75
                if instrument==17:
                    self.dof = value/-32.0
                    if(self.dof==0.0):
                        self.dof = 0.001
                if instrument==6:
                    self.ppx = (value/20.0)-1.75
                if instrument==18:
                    self.ppy = value/-32.0
                    if(self.ppy==0.0):
                        self.ppy = 0.001
                print bank,instrument,value, int(value*7.88)
            else:
                break
        if gotpkg:
            self.repaint()
        
    def paintEvent(self, event):
        #mtx = self.mtx
        mtx = QTransform()
        mtx.rotate(self.mrotation)
        mtx.scale(self.mscale.x(), self.mscale.y())
        mtx.translate(self.mtranslate.x(), self.mtranslate.y())
        eyepos = QPointF(self.epx, self.dof)
        ppoi = QPointF(self.ppx, self.ppy)
        point = QRectF(0.0,0.0,0.05,0.05);

        tpoi = mtx.map(ppoi)
        teyepos = mtx.map(eyepos)
        evec = QVector2D(tpoi - teyepos).normalized()

        pts = find_points(float2(tpoi.x(),tpoi.y()), float2(evec.x(), evec.y()))
        print pts
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.scale(self.width()/5.0,self.height()/5.0)
        qp.translate(2.5,2.5)
        #draw voxel bounds
        qp.drawRect(QRectF(0.0,0.0,1.0,1.0))
        #qp.transform(mtx)
        #draw eyepos
        point.moveTo(mtx.map(eyepos))
        qp.fillRect(point, QColor("black"))
        point.moveTo(mtx.map(ppoi))
        qp.fillRect(point, QColor("grey"))
        qp.setPen(QColor("cyan"))
        qp.drawLine(mtx.map(QLineF(-0.5,0.0,1.5,0.0)))
        qp.setPen(QColor("blue"))
        qp.drawLine(mtx.map(QLineF(-0.0,0.0,1.0,0.0)))
        qp.setPen(QColor("lime"))
        qp.drawLine(QLineF(eyepos,ppoi))
        qp.setPen(QColor("green"))
        qp.drawLine(QLineF(teyepos,tpoi))
        qp.setPen(QColor("orange"))
        qp.drawLine(QLineF(pts['x'],pts['y'],pts['z'], pts['w']))
        point.moveTo(QPointF(pts['x'],pts['y']))
        qp.fillRect(point, QColor("red"))
        point.moveTo(QPointF(pts['z'],pts['w']))
        qp.fillRect(point, QColor("pink"))
        qp.end()
        
    def drawText(self, event, qp):
      
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setFont(QtGui.QFont('Decorative', 10))
        qp.drawText(event.rect(), QtCore.Qt.AlignCenter, self.text)        
                
        
def main():    
    global has_midi
    app = QtGui.QApplication(sys.argv)
    print "Get devinfo"
    if has_midi:
        interf,name,inp,outp,opened = pypm.GetDeviceInfo(0)
    print "Got devinfo"
    ex = Example()

    atexit.register(ex.saveFile)
    atexit.register(app.exec_)


if __name__ == '__main__':
    main()

