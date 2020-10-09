#!/etc/python2.7
import sys, os, time, sprites
from PyQt4 import QtGui, QtCore
from pybrain.tools.shortcuts import buildNetwork



def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

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



class Mico_Brain():
    pass


class Mico_Body(sprites.Sprite):
    pass


class Mico():
    pass
