# Frame for peri-stimulus time histogram analysis.
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from __future__ import division
import wx
import threading
import Pyro.core
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib import pylab

from ..DataProcessing.Fitting import GaussFit,SinusoidFit,GaborFit
from ..SpikeData import TimeHistogram
from Base import UpdateDataThread,UpdateFileDataThread,RestartDataThread
from Base import EVT_DATA_START_TYPE,EVT_DATA_STOP_TYPE,EVT_DATA_RESTART_TYPE
from Base import MainFrame,DataForm,adjust_spines

class PSTHPanel(wx.Panel):
    """ Bar charts of spiking latency and instant firing rate.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(PSTHPanel, self).__init__(parent, -1, name=name)
        
        self.show_errbar_changed = False
        self.showing_errbar = False
        self.fitting_gaussian = False
        self.fitting_sinusoid = False
        self.fitting_gabor = False
        self.append_data_curve = False
        self.data_curves = 1
        self.data_point_styles = ['g.','r.','b.']
        self.fitting_curve_styles = ['g-','r--','b-.']
        
        self.psth = None
        self.start_data()
        self.raw_data = None
        
        # layout sizer
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        # data form
        self.data_form = DataForm(self, 'Data form')
        
        # canvas
        self.dpi = 100
        self.fig = Figure((8.0, 6.0), dpi=self.dpi, facecolor='w')
        self.canvas = FigCanvas(self, -1, self.fig)      
        self.make_chart()
        
        # layout hbox 
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.canvas, 0, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP, border=5)
        hbox.Add(self.data_form, 0, flag=wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_TOP, border=5)
        
        sizer.Add(hbox, 0, wx.ALIGN_CENTRE)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(1000)

    def make_chart(self,data=np.zeros(1),bins=np.arange(10)+1,polar=False,fitting=False):
        self.polar_chart = polar
        self.hist_bins = []
        self.hist_patches = []
        self.x = np.arange(17)
        self.means = np.zeros(self.x.size)
        self.stds = np.zeros(self.x.size)
        
        self.fitting_x = np.linspace(self.x[0], self.x[-1], 100, endpoint=True)
        self.fitting_y = np.zeros(self.fitting_x.size)
        self.fig.clear()
        
        grid = 18
        height = grid // 9
        gs = gridspec.GridSpec(grid, grid)
        # make tuning curve plot
        axes = self.fig.add_subplot(gs[:-height*2,height//2:-height//2],polar=polar)
        if polar:
            self.curve_data = axes.plot(self.x, self.means, 'ko-')[0]
        else:
            adjust_spines(axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=10,youtward=30,\
                          xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=5,xminor_auto_loc=2,yminor_auto_loc=2)
            axes.set_ylabel('Response(spikes/sec)',fontsize=12)
            self.curve_data = axes.plot(self.x, self.means, self.data_point_styles[0])[0]
        self.errbars = axes.errorbar(self.x, self.means, yerr=self.stds, fmt='k.') if self.showing_errbar else None
        self.curve_axes = axes
        #if fitting:
        self.fitting_data = axes.plot(self.fitting_x, self.fitting_y, self.fitting_curve_styles[0])[0]
        
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
                
        self.fig.canvas.draw()
        
    def update_chart(self, data=None):
        if data is None and hasattr(self, 'data'):
            data = self.data
        else:
            self.data = data
        if self.psth is None:
            return
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit is not None:
            channel, unit = selected_unit
            zeroth_psth_data = None
            if channel not in data or unit not in data[channel]:
                return
            polar_dict = {'orientation':True, 'spatial_frequency':False, 'phase':False, 'disparity':False}
            self.parameter = self.psth.parameter
            if self.parameter in polar_dict:
                polar_chart = polar_dict[self.parameter]
            else:
                polar_chart = self.polar_chart
            # histogram
            for index in filter(lambda index: not index & 1, data[channel][unit].iterkeys()):
                patch_index = index // 2
                spike_times = data[channel][unit][index]['spikes']
                bins = data[channel][unit][index]['bins']
                psth_data = data[channel][unit][index]['psth_data']
                if index == 0:
                    zeroth_psth_data = psth_data
                _trials = data[channel][unit][index]['trials']
                self.show_fitting_changed = False
                if len(bins) != len(self.hist_bins[0]) or self.show_errbar_changed or polar_chart != self.polar_chart:
                    self.make_chart(spike_times, bins, polar_chart, self.fitting_gaussian or self.fitting_sinusoid or self.fitting_gabor)
                    self.show_errbar_changed = False
                    self.show_fitting_changed = False
                else:
                    for rect,h in zip(self.hist_patches[patch_index],psth_data):
                        rect.set_height(h)
            
            for index in data[channel][unit].iterkeys():
                mean = data[channel][unit][index]['mean']
                std = data[channel][unit][index]['std']
                self.means[index] = mean
                self.stds[index] = std
            
            self.curve_axes.set_xscale('linear')
            
            if self.parameter == 'orientation':
                self.x = np.linspace(0.0, 360.0, 17)/180*np.pi
                self.curve_axes.set_title('Orientation Tuning Curve',fontsize=12)
                if zeroth_psth_data is not None:
                    for rect,h in zip(self.hist_patches[-1],zeroth_psth_data):
                        rect.set_height(h)
                self.means[-1] = self.means[0]
                self.stds[-1] = self.stds[0]
            if self.parameter == 'spatial_frequency':
                self.x = np.logspace(-1.0,0.5,16)
                self.curve_axes.set_title('Spatial Frequency Tuning Curve',fontsize=12)
                self.curve_axes.set_xscale('log')
                self.means = self.means[:len(self.x)]
                self.stds = self.stds[:len(self.x)]
                adjust_spines(self.curve_axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=10,youtward=30,\
                              xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=5,xminor_auto_loc=2,yminor_auto_loc=2,xmajor_loc=[0.1,0.5,1.0,2.0])
            if self.parameter in ('disparity','phase'):
                self.x = np.linspace(0.0, 360.0, 17)
                if self.parameter == 'disparity':
                    self.curve_axes.set_title('Disparity Tuning Curve',fontsize=12)
                if self.parameter == 'phase':
                    self.curve_axes.set_title('Phase Tuning Curve',fontsize=12)
                if zeroth_psth_data is not None:
                    for rect,h in zip(self.hist_patches[-1],zeroth_psth_data):
                        rect.set_height(h)
                self.means[-1] = self.means[0]
                self.stds[-1] = self.stds[0]
                adjust_spines(self.curve_axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=10,youtward=30,\
                              xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=5,xminor_auto_loc=2,yminor_auto_loc=2)
            
            if self.append_data_curve:
                self.curve_axes.plot(self.x, self.means, self.data_point_styles[self.data_curves-1])
            else:
                self.curve_data.set_xdata(self.x)
                self.curve_data.set_ydata(self.means)
            if self.errbars is not None:
                self._update_errbars(self.errbars,self.x,self.means,self.stds)
                
            self.fitting_x = np.linspace(self.x[0], self.x[-1], self.fitting_x.size, endpoint=True)
            model = np.zeros(self.fitting_x.size)
            if self.fitting_gaussian:
                model = self.gauss_fitter.gaussfit1d(self.x, self.means, self.fitting_x)
            elif self.fitting_sinusoid:
                model = self.sinusoid_fitter.sinusoid1d(self.x, self.means, self.fitting_x)
            elif self.fitting_gabor:
                model = self.gabor_fitter.gaborfit1d(self.x, self.means, self.fitting_x)
            if self.append_data_curve:
                self.curve_axes.plot(self.fitting_x, model, self.fitting_curve_styles[self.data_curves-1])
            else:
                self.fitting_data.set_xdata(self.fitting_x)
                self.fitting_data.set_ydata(model)
            label = [self.parameter, 'rate', 'std']
            self.data_form.gen_curve_data(self.x, self.means, self.stds, self.fitting_x, model, label)
            if self.parameter == 'orientation':
                self.data_form.gen_psth_data(data[channel][unit])
            self.curve_axes.set_xlim(min(self.x),max(self.x))
            self.curve_axes.set_ylim(auto=True)
            #self.curve_axes.set_ylim(0,100)
            self.curve_axes.relim()
            self.curve_axes.autoscale_view(scalex=False, scaley=True)
                
        self.fig.canvas.draw()
    
    def _update_errbars(self, errbar, x, means, yerrs):
        errbar[0].set_data(x,means)
        # Find the ending points of the errorbars
        error_positions = (x,means-yerrs), (x,means+yerrs)
        # Update the caplines
        for i,pos in enumerate(error_positions):
            errbar[1][i].set_data(pos)
        # Update the error bars
        errbar[2][0].set_segments(np.array([[x, means-yerrs], [x, means+yerrs]]).transpose((2, 0, 1)))
    
    def on_update_data_timer(self, event):
        if self.collecting_data and self.connected_to_server:
            self.update_data_thread = UpdateDataThread(self, self.psth)
            self.update_data_thread.start()
        
    def start_data(self):
        if self.psth is None:
            self.psth = TimeHistogram.PSTHAverage()
        self.collecting_data = True
        self.connected_to_server = True
    
    def stop_data(self):
        self.collecting_data = False
        
    def restart_data(self):
        self.collecting_data = False
        self.clear_data()
        if hasattr(self, 'update_data_thread') and self.psth is not None:
            restart_data_thread = RestartDataThread(self, self.psth, self.update_data_thread)
            restart_data_thread.start()
        self.collecting_data = True
    
    def gaussianfit(self, checked):
        self.gauss_fitter = GaussFit()
        self.fitting_gaussian = checked
        
    def sinusoidfit(self, checked):
        self.sinusoid_fitter = SinusoidFit()
        self.fitting_sinusoid = checked
        
    def gaborfit(self, checked):
        self.gabor_fitter = GaborFit()
        self.fitting_gabor = checked
    
    def show_errbar(self, checked):
        self.show_errbar_changed = True
        self.showing_errbar = checked
    
    def on_show_popup(self, event):
        pos = event.GetPosition()
        pos = event.GetEventObject().ScreenToClient(pos)
        self.PopupMenu(self.popup_menu, pos)
    
    def open_file(self, path, callback=None):
        self.psth = TimeHistogram.PSTHAverage(path)
        data_thread = UpdateFileDataThread(self, self.psth, callback)
        data_thread.start()
        self.connected_to_server = False
    
    def append_data(self, path, callback=None):
        self.append_data_curve = True
        self.data_curves += 1
        self.open_file(path, callback)
        
    def clear_data(self):
        self.make_chart()
        wx.FindWindowByName('main_frame').unit_choice.clear_unit()
        self.data_form.clear_data()
    
    def save_data(self):
        data_dict = {}
        data_dict['stimulus'] = self.psth.parameter
        data_dict['x'] = self.x
        data_dict['y'] = self.means
        data_dict['data'] = self.data
        return data_dict
    
    def save_chart(self,path):
        self.canvas.print_figure(path, dpi=self.dpi)

class PSTHFrame(MainFrame):
    """ The main frame of the application
    """
    def __init__(self):
        self.title = 'Peri-Stimulus Time Histogram(PSTH) Average'
        super(PSTHFrame, self).__init__(self.title)
        
    def create_menu(self):
        super(PSTHFrame, self).create_menu()
        
        self.menu_fitting = wx.Menu()
        self.m_gaussfitter = self.menu_fitting.AppendCheckItem(-1, "Ga&ussian\tCtrl-U", "Gaussian curve")
        self.menu_fitting.Check(self.m_gaussfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaussfitter, self.m_gaussfitter)
        self.m_sinfitter = self.menu_fitting.AppendCheckItem(-1, "&Sinusoidal\tCtrl-S", "Sinusoidal curve")
        self.menu_fitting.Check(self.m_sinfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_sinfitter, self.m_sinfitter)
        self.m_gaborfitter = self.menu_fitting.AppendCheckItem(-1, "Ga&bor\tCtrl-B", "Gabor curve")
        self.menu_fitting.Check(self.m_gaborfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaborfitter, self.m_gaborfitter)
        self.menu_uncheck_binds = {self.m_gaussfitter.GetId():self.uncheck_gaussfitter,\
                                   self.m_sinfitter.GetId():self.uncheck_sinfitter,\
                                   self.m_gaborfitter.GetId():self.uncheck_gaborfitter}
        
        self.menu_view = wx.Menu()
        self.m_errbar = self.menu_view.AppendCheckItem(-1, "&Errorbar\tCtrl-E", "Display errorbar")
        self.menu_view.Check(self.m_errbar.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_errbar, self.m_errbar)
        
        self.menubar.Append(self.menu_fitting, "&Fitting")
        self.menubar.Append(self.menu_view, "&View")
        self.SetMenuBar(self.menubar)
        
    def create_chart_panel(self):
        self.chart_panel = PSTHPanel(self.panel, 'PSTH Chart')
    
    def on_data_updated(self, event):
        data = event.get_data()
        self.unit_choice.update_units(data)
        self.chart_panel.update_chart(data)
        
    def on_check_gaussfitter(self, event):
        if self.m_gaussfitter.IsChecked():
            for item in self.menu_fitting.GetMenuItems():
                if item.GetId() != self.m_gaussfitter.GetId() and item.IsChecked():
                    self.menu_fitting.Check(item.GetId(), False)
                    self.menu_uncheck_binds[item.GetId()]()
            self.flash_status_message("Using gaussian fitting")
        self.chart_panel.gaussianfit(self.m_gaussfitter.IsChecked())
        self.chart_panel.update_chart()
        
    def uncheck_gaussfitter(self):
        self.chart_panel.gaussianfit(False)
        
    def on_check_sinfitter(self, event):
        if self.m_sinfitter.IsChecked():
            for item in self.menu_fitting.GetMenuItems():
                if item.GetId() != self.m_sinfitter.GetId() and item.IsChecked():
                    self.menu_fitting.Check(item.GetId(), False)
                    self.menu_uncheck_binds[item.GetId()]()
            self.flash_status_message("Using sinusoidal fitting")
        self.chart_panel.sinusoidfit(self.m_sinfitter.IsChecked())
        self.chart_panel.update_chart()
        
    def uncheck_sinfitter(self):
        self.chart_panel.sinusoidfit(False)
        
    def on_check_gaborfitter(self, event):
        if self.m_gaborfitter.IsChecked():
            for item in self.menu_fitting.GetMenuItems():
                if item.GetId() != self.m_gaborfitter.GetId() and item.IsChecked():
                    self.menu_fitting.Check(item.GetId(), False)
                    self.menu_uncheck_binds[item.GetId()]()
            self.flash_status_message("Using gabor fitting")
        self.chart_panel.gaborfit(self.m_gaborfitter.IsChecked())
        self.chart_panel.update_chart()
        
    def uncheck_gaborfitter(self):
        self.chart_panel.gaborfit(False)
        
    def uncheck_fitting(self):
        for item in self.menu_fitting.GetMenuItems():
            self.menu_fitting.Check(item.GetId(), False)
            self.menu_uncheck_binds[item.GetId()]()
        self.chart_panel.update_chart()
        
    def on_check_errbar(self, event):
        if self.m_errbar.IsChecked():
            self.chart_panel.show_errbar(True)
            self.flash_status_message("Showing error bar")
        else:
            self.chart_panel.show_errbar(False)
            self.flash_status_message("Stoped showing error bar")
        self.chart_panel.update_chart()

class DataRestartEvent(wx.PyCommandEvent):
    pass        

class RCPSTHPanel(PSTHPanel, Pyro.core.ObjBase):
    """
        Remote controlled PSTH panel
    """
    def __init__(self, *args,**kwargs):
        PSTHPanel.__init__(self,*args,**kwargs)
        Pyro.core.ObjBase.__init__(self)
        
        # handle request from pyro client
        self.export_path = None
        self.start_request = False
        self.stop_request = False
        self.restart_request = False
        self.fitting_request = None
        self.unfitting_request = False
        self.errbar_request = None
        self.check_request_timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self._on_check_request, self.check_request_timer)
        self.check_request_timer.Start(500)
    
    def __del__(self):
        PSTHPanel.__del__(self)
        Pyro.core.ObjBase.__del__(self)
        
    def _on_check_request(self, event):
        self._check_export_chart()
        self._check_start_request()
        self._check_stop_request()
        self._check_restart_request()
        self._check_fitting_request()
        self._check_unfitting_request()
        self._check_errbar_request()
    
    def _check_export_chart(self):
        if self.export_path is not None:
            self.save_chart(self.export_path)
            self.export_path = None
    
    def _check_start_request(self):
        if self.start_request is not False:
            parent = wx.FindWindowByName('main_frame')
            evt = wx.CommandEvent(EVT_DATA_START_TYPE)
            wx.PostEvent(parent, evt)
            self.start_request = False
            
    def _check_stop_request(self):
        if self.stop_request is not False:
            parent = wx.FindWindowByName('main_frame')
            evt = wx.CommandEvent(EVT_DATA_STOP_TYPE)
            wx.PostEvent(parent, evt)
            self.stop_request = False
    
    def _check_restart_request(self):
        if self.restart_request is not False:
            parent = wx.FindWindowByName('main_frame')
            #evt = DataRestartEvent(EVT_DATA_RESTART_TYPE, -1)
            evt = wx.CommandEvent(EVT_DATA_RESTART_TYPE)
            wx.PostEvent(parent, evt)
            self.restart_request = False
            
    def _check_fitting_request(self):
        if self.fitting_request is not None:
            evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
            parent = wx.FindWindowByName('main_frame')
            if self.fitting_request == 'gauss':
                parent.menu_fitting.Check(parent.m_gaussfitter.GetId(), True)
                evt.SetId(parent.m_gaussfitter.GetId())
                wx.PostEvent(parent, evt)
            if self.fitting_request == 'sin':
                parent.menu_fitting.Check(parent.m_sinfitter.GetId(), True)
                evt.SetId(parent.m_sinfitter.GetId()) 
                wx.PostEvent(parent, evt)
            if self.fitting_request == 'gabor':
                parent.menu_fitting.Check(parent.m_gaborfitter.GetId(), True)
                evt.SetId(parent.m_gaborfitter.GetId()) 
                wx.PostEvent(parent, evt)
            self.fitting_request = None
        
    def _check_unfitting_request(self):
        if self.unfitting_request is not False:
            parent = wx.FindWindowByName('main_frame')
            parent.uncheck_fitting()
            self.unfitting_request = False
            
    def _check_errbar_request(self):
        if self.errbar_request is not None:
            evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
            parent = wx.FindWindowByName('main_frame')
            parent.menu_view.Check(parent.m_errbar.GetId(), self.errbar_request)
            evt.SetId(parent.m_errbar.GetId())
            wx.PostEvent(parent, evt)
            self.errbar_request = None
    
    def get_data(self):
        return self.data_form.get_data()
    
    def export_chart(self, path):
        self.export_path = path
        
    def start_psth(self):
        self.start_request = True
        
    def stop_psth(self):
        self.stop_request = True
        
    def restart_psth(self):
        self.restart_request = True
        
    def check_fitting(self, fitting):
        # fitting in ('gauss','sin','gabor')
        self.fitting_request = fitting
    
    def uncheck_fitting(self):
        self.unfitting_request = True
        
    def check_errbar(self, checked):
        self.errbar_request = checked
        
class PyroPSTHFrame(PSTHFrame):
    """
        Remote controlled PSTH frame
    """
    def create_chart_panel(self):
        self.chart_panel = RCPSTHPanel(self.panel, 'PSTH Chart')
        threading.Thread(target=self.create_pyro_server).start()
        
    def create_pyro_server(self):
        Pyro.config.PYRO_MULTITHREADED = 1
        Pyro.core.initServer()
        self.pyro_daemon = Pyro.core.Daemon(port=6743)
        self.PYRO_URI = self.pyro_daemon.connect(self.chart_panel, 'psth_server')
        print self.PYRO_URI
        self.pyro_daemon.requestLoop()
    
    def on_exit(self, event):
        self.pyro_daemon.disconnect(self.chart_panel)
        self.pyro_daemon.shutdown()
        super(PyroPSTHFrame, self).on_exit(event)
        
        