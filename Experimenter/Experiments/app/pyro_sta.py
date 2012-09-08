#!/usr/bin/python
# STA server
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import sys
import wx
from Experimenter.GUI.STAverage import PyroSTAFrame

def launch_sta_app(port=6878):
    app = wx.PySimpleApp()
    frame = PyroSTAFrame(pyro_port=port)
    frame.Show()
    app.SetTopWindow(frame)
    app.MainLoop()

if __name__ == '__main__':
    port = int(sys.argv[-1])
    launch_sta_app(port)
