# Plot receptive field structure obtained by spike triggered average.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import wx
from Experimenter.GUI.STAverage import STAFrame

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = STAFrame()
    app.frame.Show()
    app.MainLoop()
