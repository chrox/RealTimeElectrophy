# PSTH average analysis for orientation tuning/ spatial frequency tuning and disparity tuning experiment.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.
from __future__ import division
import wx
import numpy as np
import threading
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib import pylab

from Experimenter.GUI.DataCollect import UpdateDataThread,RestartDataThread
from Experimenter.GUI.DataCollect import MainFrame,adjust_spines
from Experimenter.TimeHistogram import TimeHistogram

class PSTHPanel(wx.Panel):
    """ Bar charts of spiking latency and instant firing rate.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(PSTHPanel, self).__init__(parent, -1, name=name)
        
        self.collecting_data = False
        self.connected_to_server = False
        self.data_started = False
        self.show_errbar_changed = False
        self.showing_errbar = False
        
        self.psth = None
        self.raw_data = None

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
        self.update_data_timer.Start(1000)

    def make_chart(self,data=np.zeros(1),bins=np.arange(10)+1,polar=False):
        self.polar_chart = polar
        self.hist_bins = []
        self.hist_patches = []
        self.x = np.arange(17)
        self.means = np.zeros(17)
        self.stds = np.zeros(17)
        self.fig.clear()
        grid = 18
        height = grid // 9
        gs = gridspec.GridSpec(grid, grid)
        # make tuning curve plot
        axes = self.fig.add_subplot(gs[:-height*2,height//2:-height//2],polar=polar)
        if not polar:
            adjust_spines(axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=10,youtward=30,\
                          xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=5,xminor_auto_loc=2,yminor_auto_loc=2)
            axes.set_ylabel('Response(spikes/sec)',fontsize=12)
        self.curve_data = axes.plot(self.x, self.means, 'ko-')[0]
        self.errbars = axes.errorbar(self.x, self.means, yerr=self.stds, fmt='k.') if self.showing_errbar else None
        self.curve_axes = axes
        axes.set_ylim(0,100)
        axes.relim()
        axes.autoscale_view(scalex=True, scaley=False)
        axes.grid(b=True, which='major',axis='both',linestyle='-.')
        # make histgrams plot
        rows,cols = (grid-height,grid)
        for row in range(rows,cols)[::height]:
            for col in range(cols)[::height]:
                axes = self.fig.add_subplot(gs[row:row+height,col:col+height])
                axes.set_axis_bgcolor('white')
                #axes.set_title('PSTH', size=8)
                axes.set_ylim(0,100)
                if col == 0:
                    adjust_spines(axes,spines=['left','bottom'],xticks='bottom',yticks='left',tick_label=['y'],xaxis_loc=4,yaxis_loc=3)
                    axes.set_ylabel('Spikes',fontsize=11)
                elif col == cols-height:
                    adjust_spines(axes,spines=['right','bottom'],xticks='bottom',yticks='right',tick_label=['y'],xaxis_loc=4,yaxis_loc=3)
                else:
                    adjust_spines(axes,spines=['bottom'],xticks='bottom',yticks='none',tick_label=[],xaxis_loc=4,yaxis_loc=3)
                pylab.setp(axes.get_xticklabels(), fontsize=8)
                pylab.setp(axes.get_yticklabels(), fontsize=8)
                _n, bins, patches = axes.hist(data, bins, facecolor='black', alpha=1.0)
                self.hist_bins.append(bins)
                self.hist_patches.append(patches)
    
    def on_update_data_timer(self, event):
        if self.collecting_data and self.connected_to_server:
            self.update_data_thread = UpdateDataThread(self, self.psth)
        
    def start_data(self):
        if self.psth is None:
            self.psth = TimeHistogram.PSTHAverage()
        self.collecting_data = True
        self.connected_to_server = True
    
    def stop_data(self):
        self.collecting_data = False
        
    def restart_data(self):
        self.collecting_data = False
        self.make_chart()
        self.psth = TimeHistogram.PSTHAverage()
        if hasattr(self, 'update_data_thread') and self.psth is not None:
            RestartDataThread(self, self.psth, self.update_data_thread)
        self.collecting_data = True
    
    def show_errbar(self, checked):
        self.show_errbar_changed = True
        self.showing_errbar = checked
    
    def on_show_popup(self, event):
        pos = event.GetPosition()
        pos = event.GetEventObject().ScreenToClient(pos)
        self.PopupMenu(self.popup_menu, pos)
    
    def open_file(self, path):
        self.psth = TimeHistogram.PSTHAverage(path)
        UpdateDataThread(self, self.psth)
        self.connected_to_server = False
    
    def save_data(self):
        data_dict = {}
        data_dict['stimulus'] = self.psth.parameter
        data_dict['x'] = self.x
        data_dict['y'] = self.means
        data_dict['data'] = self.data
        return data_dict
    
    def save_chart(self,path):
        self.canvas.print_figure(path, dpi=self.dpi)
            
class UpdateChartThread(threading.Thread):
    def __init__(self, panel, data=None):
        threading.Thread.__init__(self)
        if data is None and hasattr(panel, 'data'):
            data = panel.data
        if panel.psth is None:
            return
        self.panel = panel
        self.parameter = panel.psth.parameter
        
        self.hist_bins = panel.hist_bins
        self.hist_patches = panel.hist_patches
        self.errbars = panel.errbars
        self.curve_data = panel.curve_data
        self.curve_axes = panel.curve_axes
        
        self._data = data
        self.run()
    def run(self):
        self.update_chart(self.panel, self._data)
        
    def update_chart(self, panel, data):
        panel.data = data
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit is not None:
            channel, unit = selected_unit
            zeroth_psth_data = None
            if channel not in data or unit not in data[channel]:
                return
            polar_dict = {'orientation':True, 'spatial_frequency':False, 'phase':False}
            if self.parameter in polar_dict:
                polar_chart = polar_dict[self.parameter]
            else:
                polar_chart = panel.polar_chart
            # histogram
            for index in filter(lambda index: not index & 1, data[channel][unit].iterkeys()):
                patch_index = index // 2
                spike_times = data[channel][unit][index]['spikes']
                bins = data[channel][unit][index]['bins']
                psth_data = data[channel][unit][index]['psth_data']
                if index == 0:
                    zeroth_psth_data = psth_data
                _trials = data[channel][unit][index]['trials']
                if len(bins) != len(self.hist_bins[0]) or panel.show_errbar_changed or polar_chart != panel.polar_chart:
                    panel.make_chart(spike_times, bins, polar_chart)
                    self.hist_bins = panel.hist_bins        # update variables in panel after new chart
                    self.hist_patches = panel.hist_patches
                    self.errbars = panel.errbars
                    self.curve_data = panel.curve_data
                    self.curve_axes = panel.curve_axes
                    panel.show_errbar_changed = False
                else:
                    for rect,h in zip(self.hist_patches[patch_index],psth_data):
                        rect.set_height(h)
            
            for index in data[channel][unit].iterkeys():
                mean = data[channel][unit][index]['mean']
                std = data[channel][unit][index]['std']
                panel.means[index] = mean
                panel.stds[index] = std
                
            if self.parameter == 'orientation':
                panel.x = np.linspace(0.0, 360.0, 17)/180*np.pi
                self.curve_axes.set_title('Orientation Tuning Curve',fontsize=12)
                if zeroth_psth_data is not None:
                    for rect,h in zip(self.hist_patches[-1],zeroth_psth_data):
                        rect.set_height(h)
                panel.means[-1] = panel.means[0]
                panel.stds[-1] = panel.stds[0]
            if self.parameter == 'spatial_frequency':
                panel.x = np.linspace(0.05, 1.0, 16)
                self.curve_axes.set_title('Spatial Frequency Tuning Curve',fontsize=12)
                panel.means = panel.means[:len(panel.x)]
                panel.stds = panel.stds[:len(panel.x)]
            if self.parameter == 'phase':
                panel.x = np.linspace(0.0, 360.0, 17)
                self.curve_axes.set_title('Disparity Tuning Curve',fontsize=12)
                if zeroth_psth_data is not None:
                    for rect,h in zip(self.hist_patches[-1],zeroth_psth_data):
                        rect.set_height(h)
                panel.means[-1] = panel.means[0]
                panel.stds[-1] = panel.stds[0]
            
            self.curve_data.set_xdata(panel.x)
            self.curve_data.set_ydata(panel.means)
            if self.errbars is not None:
                self._update_errbars(self.errbars,panel.x,panel.means,panel.stds)
                
            self.curve_axes.set_xlim(min(panel.x),max(panel.x))
            self.curve_axes.set_ylim(auto=True)
            #self.curve_axes.set_ylim(0,100)
            self.curve_axes.relim()
            self.curve_axes.autoscale_view(scalex=False, scaley=True)
        panel.fig.canvas.draw()
    
    def _update_errbars(self, errbar, x, means, yerrs):
        errbar[0].set_data(x,means)
        # Find the ending points of the errorbars
        error_positions = (x,means-yerrs), (x,means+yerrs)
        # Update the caplines
        for i,pos in enumerate(error_positions):
            errbar[1][i].set_data(pos)
        # Update the error bars
        errbar[2][0].set_segments(np.array([[x, means-yerrs], [x, means+yerrs]]).transpose((2, 0, 1)))

class PSTHFrame(MainFrame):
    """ The main frame of the application
    """
    def __init__(self):
        title = 'Peri-Stimulus Time Histogram(PSTH) Average'
        super(PSTHFrame, self).__init__(title)
        
    def create_menu(self):
        super(PSTHFrame, self).create_menu()
        
        menu_view = wx.Menu()
        self.m_errbar = menu_view.AppendCheckItem(-1, "&Errorbar\tCtrl-E", "Display errorbar")
        menu_view.Check(self.m_errbar.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_errbar, self.m_errbar)
        
        self.menubar.Append(menu_view, "&View")
        self.SetMenuBar(self.menubar)
        
    def create_chart_panel(self):
        self.chart_panel = PSTHPanel(self.panel, 'PSTH Chart')
    
    def on_data_updated(self, event):
        data = event.get_data()
        self.unit_choice.update_units(data)
        UpdateChartThread(self.chart_panel, data)
        
    def on_check_errbar(self, event):
        if self.m_errbar.IsChecked():
            self.chart_panel.show_errbar(True)
            self.flash_status_message("Showing error bar")
        else:
            self.chart_panel.show_errbar(False)
            self.flash_status_message("Stoped showing error bar")
        UpdateChartThread(self.chart_panel)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = PSTHFrame()
    app.frame.Show()
    app.MainLoop()
