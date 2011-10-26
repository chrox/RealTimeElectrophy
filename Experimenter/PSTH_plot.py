# Dynamic graph for peri-stimulus time histogram.
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import os
import wx
import numpy as np

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib import pylab

from Experimenter.TimeHistogram import PSTH

class UnitChoice(wx.Panel):
    """ A listbox of available channels and units.
    """
    def __init__(self, parent, label, name='unit_choice'):
        super(UnitChoice, self).__init__(parent, -1, name=name)

        self.unit_list = wx.ListBox(parent=self, size=(100,300))
        self.unit_list.Bind(wx.EVT_LISTBOX, self.on_select, self.unit_list)
        #self.unit_list.SetSelection(0)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.unit_list, 0, flag=wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_select(self,event):
        wx.FindWindowByName('psth_panel').update_chart()
        index = self.unit_list.GetSelection()
        wx.FindWindowByName('main_frame').flash_status_message("Select unit: %s" % self.items[index])

    def update_units(self,results):
        selected_unit = self.get_selected_unit()
        self.units = [(channel,unit) for channel in sorted(results.iterkeys(),key=int) for unit in sorted(results[channel].iterkeys())]
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

class PSTHPanel(wx.Panel):
    """ Bar charts of spiking latency and instant firing rate.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(PSTHPanel, self).__init__(parent, -1, name=name)

        self.psth = PSTH()
        #self.data = self.psth.get_data()
        
        self.dpi = 100
        self.fig = Figure((8.0, 3.0), dpi=self.dpi, facecolor='w')
        self.canvas = FigCanvas(self, -1, self.fig)
        self.make_chart()

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.canvas, 0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(500)

    def make_chart(self,data=np.zeros(1),bins=np.arange(10)+1):
        def adjust_spines(ax,spines):
            for loc, spine in ax.spines.iteritems():
                if loc not in spines:
                    spine.set_color('none') # don't draw spine
                if loc in ('left','right'):
                    spine.set_position(('outward',3))
            # turn off ticks where there is no spine
            if 'left' in spines:
                ax.yaxis.set_ticks_position('left')
                ax.yaxis.set_tick_params(direction='out')
                ax.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(5))
            elif 'right' in spines:
                ax.yaxis.set_ticks_position('right')
                ax.yaxis.set_tick_params(direction='out')
                ax.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(5))
            else:
                ax.yaxis.set_ticks([])
                
            if 'bottom' in spines:
                ax.xaxis.set_ticks_position('bottom')
                ax.xaxis.set_ticklabels([])
                ax.xaxis.set_tick_params(direction='out')
                ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(4))
            else:
                ax.xaxis.set_ticks([])
                
        self.default_bins = []
        self.patches = []
        self.fig.clf()
        row,col = (2,8)
        for i in range(row*col):
            axes = self.fig.add_subplot(row,col,i+1)
            axes.set_axis_bgcolor('white')
            #axes.set_title('PSTH', size=8)
            
            axes.set_ylim(0,200)
            if i in np.arange(row)*col:
                adjust_spines(axes,['left','bottom'])
                axes.set_ylabel('spikes/sec')
            elif i in np.arange(1,row+1)*col-1:
                adjust_spines(axes,['right','bottom'])
            else:
                adjust_spines(axes,['bottom'])
            pylab.setp(axes.get_xticklabels(), fontsize=8)
            pylab.setp(axes.get_yticklabels(), fontsize=8)
            _n, bins, patches = axes.hist(data, bins, facecolor='black', alpha=1.0)
            self.default_bins.append(bins)
            self.patches.append(patches)
            
    def update_chart(self):
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            for index in self.data[channel][unit].iterkeys():
                spike_times = self.data[channel][unit][index]['spikes']
                bins = self.data[channel][unit][index]['bins']
                psth_data = self.data[channel][unit][index]['psth_data']
                _trials = self.data[channel][unit][index]['trials']
                _mean = self.data[channel][unit][index]['mean']
                _std = self.data[channel][unit][index]['std']
                if len(bins) is not len(self.default_bins[0]):
                    self.make_chart(spike_times, bins)
                else:
                    for rect,h in zip(self.patches[index],psth_data):
                        rect.set_height(h)
            self.fig.canvas.draw()

    def on_update_data_timer(self, event):
        # update bars data and units
        #self.results = self.response.get_demo_results()
        self.data = self.psth.get_data()
        wx.FindWindowByName('unit_choice').update_units(self.data)

    def on_save_chart(self, event):
        file_choices = "PNG (*.png)|*.png"
        dlg = wx.FileDialog(
            self,
            message="Save chart as...",
            defaultDir=os.getcwd(),
            defaultFile="psth.png",
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
        title = 'Peri-stimulus time histogram(PSTH)'
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        #style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, pos=(50,50), style=style, name='main_frame')

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(500)

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
        self.psth_chart= PSTHPanel(self.panel, 'PSTH Chart')

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.unit_choice, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border=5)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.psth_chart, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_CENTER_VERTICAL, border=5)
        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)

    def on_save_chart(self, event):
        self.psth_chart.on_save_chart(event)

    def on_redraw_timer(self, event):
        """ refresh the bars
        """
        self.psth_chart.update_chart()

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
