#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2026 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0'''
from enum import *

class Orient(IntFlag):
    ''' Enum for passing an orientation '''
    PROXIMAL = 1
    DISTAL = 2
    INNER = 4
    OUTER = 8
    UNIVERSAL = 16
    MIDDLE = 32

class BumperStyle(Enum):
    NONE = 0
    MINIMAL = 2
    COVER = 4
    FULL = 8

class RenderQuality(Enum):
    ''' Enum for passing an orientation '''
    NONE = 0
    INSANE = 2
    ULTRAHIGH = 5
    EXTRAHIGH = 8
    HIGH = 10
    EXTRAMEDIUM = 12
    MEDIUM = 15
    SUBMEDIUM = 17
    FAST = 20
    ULTRAFAST = 25
    STUPIDFAST = 30

class FingerPart(IntFlag):
    ''' Enum for passing an orientation '''
    NONE = 0
    SOCKET = 1
    BASE = 2
    MIDDLE = 4
    TIP = 8
    TIPCOVER = 16
    LINKAGE = 32
    PLUG = 64
    PEG = 128
    BUMPER = 256
    STAND = 1024
    PINS = 2048
    RENDER = 8192
    PREVIEW = 16384
  #  SOFT = BUMPER | PLUG | SOCKET | TIPCOVER | PEG | PLUG
    ALL =   SOCKET | TIPCOVER | BASE | TIP | MIDDLE | LINKAGE | PEG | PLUG | BUMPER | PREVIEW | RENDER
    EXPLODE = BUMPER | PLUG | SOCKET | TIPCOVER | BASE | TIP | MIDDLE | LINKAGE | PEG | PREVIEW | PINS | STAND
   # HARD = BASE | TIP | MIDDLE | LINKAGE

    #    PLUG = 2048
    @classmethod
    def from_str(cls, label):
        ''' parse string into this enum'''
        return cls[str.upper(label)]

    def __str__(self):
        return self.name.lower()

class CustomType(IntFlag):
    ''' Enum for customizer variab;e type '''
    NONE = 0
    DROPDOWN = 2
    SLIDER = 4
    SPINNER = 8
    CHECKBOX = 16
    TEXTBOX = 32

WIDTH_ADJUSTMENTS = {
        'i': 0.5, 'l': 0.6, 't': 0.6, 'f': 0.7, 'j': 0.6, 'a': 0.97,
        ' ': 0.8, 'o': 1.2, 'e': .8, '-': .5, '.': .4
    }