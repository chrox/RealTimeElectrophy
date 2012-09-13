# PSTH average analysis for orientation tuning/ spatial frequency tuning and disparity tuning experiment.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.
import wx
from Experimenter.GUI.PSTHTuning import PSTHTuningFrame

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = PSTHTuningFrame()
    app.frame.Show()
    app.MainLoop()
