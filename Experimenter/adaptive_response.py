# Dynamic graph for adaptive response.
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

import os
import wx
import numpy as np

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
import pylab

from Experimenter.AdaptiveResponse import AdaptiveResponse

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
        wx.FindWindowByName('bar_chart').update_chart()
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

class ChartBar(wx.Panel):
    """ Bar charts of spiking latency and instant firing rate.
    """
    def __init__(self, parent, label, name='bar_chart'):
        super(ChartBar, self).__init__(parent, -1, name=name)

        self.response = AdaptiveResponse.AdaptiveResponse()
        self.means_latency = np.array([0, 0, 0, 0])
        self.std_latency = np.array([0, 0, 0, 0])
        self.means_rate = np.array([0, 0, 0, 0])
        self.std_rate = np.array([0, 0, 0, 0])

        self.dpi = 100
        self.fig = Figure((8.0, 3.0), dpi=self.dpi, facecolor='w')
        self.canvas = FigCanvas(self, -1, self.fig)
        self.make_bars()

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.canvas, 0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(500)

    def init_bar(self,index,title,ylabel,xticklabels,barcolors,means,yerrs,bgcolor='white',ecolor='black'):
        ind = np.arange(len(means))
        width = 0.65
        # spike latency bar
        axes = self.fig.add_subplot(1,2,index)
        axes.set_axis_bgcolor(bgcolor)
        axes.set_title(title, size=12)
        axes.set_ylabel(ylabel)
        axes.set_xticks(ind)
        axes.set_xticklabels(xticklabels)
        axes.set_xlim((ind[0]-1, ind[-1]+1))
        axes.set_ylim(0,100)
        axes.spines['right'].set_color('none')
        axes.spines['top'].set_color('none')
        axes.spines['bottom'].set_color('none')
        axes.xaxis.set_ticks_position('none')
        axes.yaxis.set_ticks_position('left')
        pylab.setp(axes.get_xticklabels(), fontsize=8)
        pylab.setp(axes.get_yticklabels(), fontsize=8)
        bars = [axes.bar(ind[i], mean, width, color=barcolors[i], align='center', ecolor=ecolor) for i,mean in enumerate(means)]
        errbars = axes.errorbar(ind, means, yerr=yerrs, fmt='k.')
        return (bars, errbars, axes)

    def make_bars(self):
        xlabels = ['Left', 'Right', 'Left', 'Right']
        colors = ['#FFFFFF','#999999','#FFFFCC','#555555']
        self.latency_bars = self.init_bar(index=1,title='Spiking latency',ylabel='milliseconds',xticklabels=xlabels,barcolors=colors,means=self.means_latency,yerrs=self.std_latency)
        self.rate_bars = self.init_bar(index=2,title='Instant firing rate',ylabel='spikes/sec',xticklabels=xlabels,barcolors=colors,means=self.means_rate,yerrs=self.std_rate)

    def update_bars(self, bars_data, means, yerrs):
        for i,bars in enumerate(bars_data[0]):
            for bar in bars:
                bar.set_height(means[i])
        # update error bars
        errbar = bars_data[1]
        ind = np.arange(len(means))
        errbar[0].set_data(ind,means)
        # Find the ending points of the errorbars
        error_positions = (ind,means-yerrs), (ind,means+yerrs)
        # Update the caplines
        for i,pos in enumerate(error_positions):
            errbar[1][i].set_data(pos)
        # Update the error bars
        errbar[2][0].set_segments(np.array([[ind, means-yerrs], [ind, means+yerrs]]).transpose((2, 0, 1)))
        # scale the y axis if neccesary
        bars_data[2].set_ylim(auto=True)
        bars_data[2].relim()
        bars_data[2].autoscale_view(scalex=False, scaley=True)

    def update_chart(self):
        # chart will not be updated if:
        #    i) no unit is selected.
        #   ii) i) will be true if no data is fetched from Server.
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            self.means_latency, self.std_latency = self.results[channel][unit]['latency']
            self.means_rate, self.std_rate = self.results[channel][unit]['rate']

            self.update_bars(self.latency_bars, self.means_latency, self.std_latency)
            self.update_bars(self.rate_bars, self.means_rate, self.std_rate)
            self.canvas.draw()

    def on_update_data_timer(self, event):
        # update bars data and units
        #self.results = self.response.get_demo_results()
        self.results = self.response.get_results()
        wx.FindWindowByName('unit_choice').update_units(self.results)

    def on_save_chart(self, event):
        file_choices = "PNG (*.png)|*.png"
        dlg = wx.FileDialog(
            self,
            message="Save chart as...",
            defaultDir=os.getcwd(),
            defaultFile="adap-resp.png",
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
        title = 'adaptive response'
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        #style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, pos=(50,50), style=style, name='main_frame')
        
        path = os.path.join(os.path.dirname(AdaptiveResponse.__file__),'chart-bar-icon.png')
        icon = wx.Icon(path, wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)

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
        self.chart_bar= ChartBar(self.panel, 'Bar Chart')

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.unit_choice, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border=5)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.chart_bar, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_CENTER_VERTICAL, border=5)
        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)

    def on_save_chart(self, event):
        self.chart_bar.on_save_chart(event)

    def on_redraw_timer(self, event):
        """ refresh the bars
        """
        self.chart_bar.update_chart()

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
