#!/etc/python2.7
import sys, os, time, sprites
from PyQt4 import QtGui, QtCore



def num2perc(num, maxNum):
    perc = (float(num) / float(maxNum))
    perc = (perc * 100.0)
    return perc

def perc2num(perc, maxNum):
    num = (float(perc) / 100.0)
    num = (num * float(maxNum))
    return num

def posList(lst):
    lst2 = []
    for i in lst:
        if (i < 0):
            lst2.append(-i)
        else:
            lst2.append(i)
    return lst2

def condition(listVar):
    lst2 = []

    for i in listVar:
        i = float(i)
        isneg = False
        if (i < 0):
            isneg = True; i = -i
        i = (i / sum(posList(listVar)))
        if (isneg): i = -i
        lst2.append(i)

    return lst2



class Mico(QtGui.QGraphicsPixmapItem):
    pass
