# Plot receptive field structure obtained by spike triggered average.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

import os
import wx
import numpy as np
import threading
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib import cm

from Experimenter.ReverseCorrelation import RevCorr

EVT_UPDATED_TYPE = wx.NewEventType()
EVT_UPDATED = wx.PyEventBinder(EVT_UPDATED_TYPE, 1)

class DataUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, data=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._data = data
    def get_data(self):
        return self._data

class UpdateDataThread(threading.Thread):
    def __init__(self, parent, sta_data):
        threading.Thread.__init__(self)
        self._parent = parent
        self._sta_data = sta_data
        self.run()
    def run(self):
        self._data = self._sta_data.get_data()
        evt = DataUpdatedEvent(EVT_UPDATED_TYPE, -1, self._data)
        wx.PostEvent(self._parent, evt)

class UnitChoice(wx.Panel):
    """ A listbox of available channels and units.
    """
    def __init__(self, parent, label, name='unit_choice'):
        super(UnitChoice, self).__init__(parent, -1, name=name)

        self.unit_list = wx.ListBox(parent=self, size=(100,600))
        self.unit_list.Bind(wx.EVT_LISTBOX, self.on_select, self.unit_list)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.unit_list, 0, flag=wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_select(self,event):
        #wx.FindWindowByName('sta_panel').update_chart()
        index = self.unit_list.GetSelection()
        wx.FindWindowByName('main_frame').flash_status_message("Select unit: %s" % self.items[index])

    def update_units(self,data):
        selected_unit = self.get_selected_unit()
        self.units = [(channel,unit) for channel in sorted(data.iterkeys(),key=int) for unit in sorted(data[channel].iterkeys())]
        self.items = ['DSP%s%c' %(channel,unit) for channel,unit in self.units]
        self.unit_list.SetItems(self.items)
        if selected_unit:                                       # selected unit previously
            selected_index = self.units.index(selected_unit)
            self.unit_list.SetSelection(selected_index)
        elif self.items:                                        # didn't select
            self.unit_list.SetSelection(0)

    def get_selected_unit(self):
        index = self.unit_list.GetSelection()
        if index is not wx.NOT_FOUND:
            return self.units[index]

class STAPanel(wx.Panel):
    """ Receptive field plot.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(STAPanel, self).__init__(parent, -1, name=name)

        self.sta_data = RevCorr.STAData()
        # reverse time in ms
        self.time = 85
        
        self.dpi = 100
        self.fig = Figure((8.0, 6.0), dpi=self.dpi, facecolor='w')
        self.fig.subplots_adjust(wspace = 0.1,hspace = 0.1)
        self.canvas = FigCanvas(self, -1, self.fig)
        self.make_chart()

        self.slider = wx.Slider(self, -1, self.time, 0, 200, None, (250, 50), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.interpolations = ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite', \
                   'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
        self.interpolation = 'nearest'
        self.combobox = wx.ComboBox(self, -1, pos=(-1,-1), size=(150, -1), choices=self.interpolations, 
                                    style=wx.CB_READONLY)
        self.combobox.SetStringSelection('nearest')
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        # slider and combobox
        vbox = wx.BoxSizer(wx.VERTICAL)
        option_hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        option_hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        time_text = wx.StaticText(self, -1, 'Time:')
        interpolation_text = wx.StaticText(self, -1, 'Interpolation:')
        option_hbox1.Add(time_text,0,wx.LEFT)
        option_hbox1.Add(self.slider,0,wx.LEFT)
        option_hbox2.Add(interpolation_text,0,wx.LEFT)
        option_hbox2.AddSpacer(20)
        option_hbox2.Add(self.combobox,0,wx.LEFT)
        
        vbox.Add(option_hbox1,1,wx.TOP, 20)
        vbox.Add(option_hbox2,1,wx.TOP,20)
        # canvas 
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.canvas, 0, flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        hbox.Add(vbox,flag=wx.TOP)
        
        sizer.Add(hbox, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(30)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(2000)
        self.Bind(wx.EVT_SLIDER, self.sliderUpdate)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        
    def make_chart(self):
        def adjust_spines(ax,spines,spine_outward=['left','right'],xoutward=0,youtward=5,xticks='bottom',yticks='left',\
                          xtick_dir='out',ytick_dir='out',tick_label=['x','y'],xaxis_loc=None,yaxis_loc=None,
                          xminor_auto_loc=None,yminor_auto_loc=None):
            for loc, spine in ax.spines.iteritems():
                if loc not in spines:
                    spine.set_color('none') # don't draw spine
                if loc in spine_outward:
                    if loc in ['top','bottom']:
                        spine.set_position(('outward',xoutward))
                    if loc in ['left','right']:
                        spine.set_position(('outward',youtward))
            # set ticks
            if xaxis_loc:
                ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(xaxis_loc))
            if xminor_auto_loc:
                ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(xminor_auto_loc))
            if xticks is 'none':
                ax.xaxis.set_ticks([])
            if 'x' not in tick_label:
                ax.xaxis.set_ticklabels([])
            ax.xaxis.set_ticks_position(xticks)
            ax.xaxis.set_tick_params(which='both',direction=xtick_dir)

            if yaxis_loc:
                ax.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(yaxis_loc))
            if yminor_auto_loc:
                ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(yminor_auto_loc))
            if yticks is 'none':
                ax.yaxis.set_ticks([])
            if 'y' not in tick_label:
                ax.yaxis.set_ticklabels([])
            ax.yaxis.set_ticks_position(yticks)
            ax.yaxis.set_tick_params(which='both',direction=ytick_dir)
            
        self.axes = self.fig.add_subplot(111)
        adjust_spines(self.axes,spines=['left','top'],spine_outward=['left','top'],xoutward=5,youtward=5,\
                      xticks='top',yticks='left',tick_label=['x','y'],xminor_auto_loc=2,yminor_auto_loc=2)
        img = np.zeros((64,64,3))
        self.img_dim = img.shape
        self.im = self.axes.imshow(img,interpolation='nearest')
    
    def update_chart(self,data):
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            img = RevCorr.STAImg.get_img(data, channel, unit, self.time/1000.0)
            if self.img_dim != img.shape or self.interpolation_changed:
                self.im = self.axes.imshow(img,interpolation=self.interpolation)
                self.img_dim = img.shape
                self.interpolation_changed = False
            else:
                self.im.set_data(img)
            self.im.autoscale()
            self.canvas.draw()

    def on_update_data_timer(self, event):
        UpdateDataThread(self, self.sta_data)

    def sliderUpdate(self, event):
        self.time = self.slider.GetValue()
    
    def OnSelect(self, event):
        index = event.GetSelection()
        if self.interpolations[index] != self.interpolation:
            self.interpolation_changed = True
        self.interpolation = self.interpolations[index]

    def on_save_chart(self, event):
        file_choices = "PNG (*.png)|*.png"
        dlg = wx.FileDialog(
            self,
            message="Save chart as...",
            defaultDir=os.getcwd(),
            defaultFile="sta_chart.png",
            wildcard=file_choices,
            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            wx.FindWindowByName('main_frame').flash_status_message("Saved to %s" % path)

class MainFrame(wx.Frame):
    """ The main frame of the application
    """
    def __init__(self):
        title = 'Spike Triggered Average(STA)'
        #style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, pos=(50,50), style=style, name='main_frame')

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.Bind(EVT_UPDATED, self.on_data_updated)

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_chart, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)

        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar(name='status_bar')

    def create_main_panel(self):
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("White")

        self.unit_choice = UnitChoice(self.panel, 'Select Unit')
        self.sta_chart= STAPanel(self.panel, 'STA chart')
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.AddSpacer(5)
        self.hbox.Add(self.unit_choice, flag=wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        self.hbox.AddSpacer(5)
        self.hbox.Add(self.sta_chart, flag=wx.EXPAND | wx.ALIGN_RIGHT| wx.ALIGN_CENTER_VERTICAL, border=15)
        self.hbox.Fit(self)
        vbox.Add(self.hbox,wx.ALIGN_CENTER_VERTICAL,border=15)
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.panel.Layout()

    def on_save_chart(self, event):
        self.sta_chart.on_save_chart(event)

    def on_data_updated(self, event):
        data = event.get_data()
        self.sta_chart.update_chart(data)
        self.unit_choice.update_units(data['spikes'])

    def on_exit(self, event):
        self.Destroy()

    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER,
            self.on_flash_status_off,
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)

    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = MainFrame()
    app.frame.Show()
    app.MainLoop()
