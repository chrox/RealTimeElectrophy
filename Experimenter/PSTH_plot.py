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
import threading
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib import pylab

from Experimenter.TimeHistogram import PSTH


EVT_UPDATED_TYPE = wx.NewEventType()
EVT_UPDATED = wx.PyEventBinder(EVT_UPDATED_TYPE, 1)

class DataUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, data=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._data = data
    def get_data(self):
        return self._data

class UpdateDataThread(threading.Thread):
    def __init__(self, parent, psth):
        threading.Thread.__init__(self)
        self._parent = parent
        self._psth = psth
        self.run()
    def run(self):
        self._data = self._psth.get_data()
        evt = DataUpdatedEvent(EVT_UPDATED_TYPE, -1, self._data)
        wx.PostEvent(self._parent, evt)

class UnitChoice(wx.Panel):
    """ A listbox of available channels and units.
    """
    def __init__(self, parent, label, name='unit_choice'):
        super(UnitChoice, self).__init__(parent, -1, name=name)

        self.unit_list = wx.ListBox(parent=self, size=(100,600))
        self.unit_list.Bind(wx.EVT_LISTBOX, self.on_select, self.unit_list)
        #self.unit_list.SetSelection(0)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.unit_list, 0, flag=wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)
        
        #self.Bind(EVT_UPDATED, self.on_data_updated)

    def on_select(self,event):
        #wx.FindWindowByName('psth_panel').update_chart()
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

class PSTHPanel(wx.Panel):
    """ Bar charts of spiking latency and instant firing rate.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(PSTHPanel, self).__init__(parent, -1, name=name)

        self.psth = PSTH()
        #self.data = self.psth.get_data()
        
        
        self.dpi = 100
        self.fig = Figure((8.0, 6.0), dpi=self.dpi, facecolor='w')
        self.canvas = FigCanvas(self, -1, self.fig)
        self.make_chart()

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.canvas, 0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(1500)

    def make_chart(self,data=np.zeros(1),bins=np.arange(10)+1):
        def adjust_spines(ax,spines,spine_outward=['left','right'],outward=3,ticks=['left','bottom'],tick_direction='out',tick_label=['x','y'],xaxis_loc=None,yaxis_loc=None):
            for loc, spine in ax.spines.iteritems():
                if loc not in spines:
                    spine.set_color('none') # don't draw spine
                if loc in spine_outward:
                    spine.set_position(('outward',outward))
            # turn off ticks where there is no spine
            if 'left' in ticks:
                ax.yaxis.set_ticks_position('left')
                ax.yaxis.set_tick_params(direction=tick_direction)
                if xaxis_loc:
                    ax.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(xaxis_loc))
            elif 'right' in ticks:
                ax.yaxis.set_ticks_position('right')
                ax.yaxis.set_tick_params(direction=tick_direction)
                if xaxis_loc:
                    ax.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(xaxis_loc))
            else:
                ax.yaxis.set_ticks([])
            if 'y' not in tick_label:
                ax.yaxis.set_ticklabels([])
            
            
            if 'top' in ticks:
                ax.xaxis.set_ticks_position('top')
                ax.xaxis.set_tick_params(direction=tick_direction)
                if yaxis_loc:
                    ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(yaxis_loc))
            elif 'bottom' in ticks:
                ax.xaxis.set_ticks_position('bottom')
                ax.xaxis.set_tick_params(direction=tick_direction)
                if yaxis_loc:
                    ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(yaxis_loc))
            else:
                ax.xaxis.set_ticks([])
            if 'x' not in tick_label:
                ax.xaxis.set_ticklabels([])

        self.hist_bins = []
        self.hist_patches = []
        self.x = np.arange(16)
        self.means = np.zeros(16)
        self.stds = np.zeros(16)
        self.fig.clf()
        gs = gridspec.GridSpec(8, 8)
        axes = self.fig.add_subplot(gs[:-3,:])
        axes.set_ylabel('Response(spikes/sec)',fontsize=12)
        adjust_spines(axes,spines=['left','bottom','right'],ticks=['left','bottom','right'],tick_label=['x','y'])
        self.curve_data = axes.plot(self.x, self.means)[0]
        self.errbars = axes.errorbar(self.x, self.means, yerr=self.stds, fmt='k.')
        self.curve_axes = axes
        #axes.set_ylim(0,200)
        rows,cols = (6,8)
        for row in range(rows,cols):
            for col in range(cols):
                axes = self.fig.add_subplot(gs[row,col])
                axes.set_axis_bgcolor('white')
                #axes.set_title('PSTH', size=8)
                axes.set_ylim(0,200)
                if col == 0:
                    adjust_spines(axes,spines=['left','bottom'],ticks=['left','bottom'],tick_label=['y'],xaxis_loc=3,yaxis_loc=4)
                    axes.set_ylabel('spikes/sec',fontsize=8)
                elif col == cols-1:
                    adjust_spines(axes,spines=['right','bottom'],ticks=['right','bottom'],tick_label=['y'],xaxis_loc=3,yaxis_loc=4)
                else:
                    adjust_spines(axes,spines=['bottom'],ticks=['bottom'],tick_label=[],xaxis_loc=3,yaxis_loc=4)
                pylab.setp(axes.get_xticklabels(), fontsize=8)
                pylab.setp(axes.get_yticklabels(), fontsize=8)
                _n, bins, patches = axes.hist(data, bins, facecolor='black', alpha=1.0)
                self.hist_bins.append(bins)
                self.hist_patches.append(patches)
    def update_chart(self, data):
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            for index in data[channel][unit].iterkeys():
                spike_times = data[channel][unit][index]['spikes']
                bins = data[channel][unit][index]['bins']
                psth_data = data[channel][unit][index]['psth_data']
                _trials = data[channel][unit][index]['trials']
                mean = data[channel][unit][index]['mean']
                std = data[channel][unit][index]['std']
                self.means[index] = mean
                self.stds[index] = std
                if len(bins) is not len(self.hist_bins[0]):
                    self.make_chart(spike_times, bins)
                else:
                    for rect,h in zip(self.hist_patches[index],psth_data):
                        rect.set_height(h)
            if self.psth.parameter is 'orientation':
                self.x = np.linspace(0.0, 180.0, 16)
            if self.psth.parameter is 'spatial_frequency':
                self.x = np.linspace(0.05, 1.0, 16)
            if self.psth.parameter is 'phase':
                self.x = np.linspace(0.0, 360.0, 16)
            self.curve_data.set_xdata(self.x)
            self.curve_data.set_ydata(self.means)
            self.update_errbars(self.errbars,self.x,self.means,self.stds)
        self.fig.canvas.draw()
    
    def update_errbars(self, errbar, x, means, yerrs):
        errbar[0].set_data(x,means)
        # Find the ending points of the errorbars
        error_positions = (x,means-yerrs), (x,means+yerrs)
        # Update the caplines
        for i,pos in enumerate(error_positions):
            errbar[1][i].set_data(pos)
        # Update the error bars
        errbar[2][0].set_segments(np.array([[x, means-yerrs], [x, means+yerrs]]).transpose((2, 0, 1)))
        self.curve_axes.set_ylim(auto=True)
        self.curve_axes.relim()
        self.curve_axes.autoscale_view(scalex=True, scaley=True)
    
    def on_update_data_timer(self, event):
        #self.data = self.psth.get_data()
        UpdateDataThread(self, self.psth)

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
        #style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, pos=(50,50), style=style, name='main_frame')

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        #self.redraw_timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        #self.redraw_timer.Start(500)
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

    def on_data_updated(self, event):
        #print event.get_data()
        data = event.get_data()
        self.psth_chart.update_chart(data)
        self.unit_choice.update_units(data)
        #event.Skip()

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
