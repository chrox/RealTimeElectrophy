#!/usr/bin/python
# PSTH server
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import sys
import wx
from Experimenter.GUI.PSTHAverage import PyroPSTHFrame

def launch_psth_app(port=6743):
    app = wx.PySimpleApp()
    frame = PyroPSTHFrame(pyro_port=port)
    frame.Show()
    app.SetTopWindow(frame)
    app.MainLoop()

if __name__ == '__main__':
    port = int(sys.argv[-1])
    launch_psth_app(port)