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
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas

from ..SpikeData import TimeHistogram
from Base import UpdateDataThread,UpdateFileDataThread
from Base import MainFrame,DataPanel,RCPanel,adjust_spines

class PSTHAverageDataPanel(DataPanel):        
    def gen_curve_data(self, bins, psth_data, maxima_indices, minima_indices):
        self.data['time'] = bins
        self.data['psth'] = psth_data
        self.data['maxima_index'] = maxima_indices
        self.data['minima_index'] = minima_indices
        self.data['maxima'] = psth_data[maxima_indices]
        self.data['minima'] = psth_data[minima_indices]
        extrema = ''
        extrema += '-'*18 + '\n'
        extrema += '{0:6}\t{1}\n'.format('Maxima','Value')
        for index in maxima_indices:
            extrema += '{0:4}\t{1:.2f}\n'.format(bins[index],psth_data[index])
        extrema += 'Minima\tValue\n'
        for index in minima_indices:
            extrema += '{0:4}\t{1:.2f}\n'.format(bins[index],psth_data[index])  
        form = extrema
        self.results.SetValue(form)

class PSTHAveragePanel(wx.Panel):
    """ Bar charts of spiking latency and instant firing rate.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(PSTHAveragePanel, self).__init__(parent, -1, name=name)
        
        self.connected_to_server = True
        self.collecting_data = True
        self.append_data_curve = False
        self.data_curves = 1
        self.data_point_styles = ['g-','r-','b-']
        
        self.psth_data = TimeHistogram.PSTHAverage()
        self.data = None
        self.raw_data = None
        self.bins = None
        self.bin_data = None
        self.curve_data = None
        self.curve_axes = None
        
        self.update_data_thread = None
        
        # layout sizer
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        # data form
        self.data_form = PSTHAverageDataPanel(self, 'Data form')
        
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
        self.update_data_timer.Start(2000)

    def make_chart(self, bins=np.arange(150), bin_data=np.zeros(150)):
        self.bins = bins
        self.bin_data = bin_data
        
        self.fig.clear()
        
        # make Average curve plot
        axes = self.fig.add_subplot(111)
        adjust_spines(axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=0,youtward=0,\
                      xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=7,xminor_auto_loc=2,yminor_auto_loc=2)
        axes.set_xlabel('Time(ms)',fontsize=12)
        axes.set_ylabel('Response(spikes/sec)',fontsize=12)
        self.curve_data = axes.plot(self.bins, self.bin_data, self.data_point_styles[0])[0]
        self.curve_axes = axes
        
        axes.set_ylim(0,100)
        axes.relim()
        axes.autoscale_view(scalex=False, scaley=False)
        #axes.grid(b=True, which='major',axis='both',linestyle='-.')
                
        self.fig.canvas.draw()
        
    def update_chart(self, data=None):
        if data is None and self.data is not None:
            data = self.data
        
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit is not None:
            channel, unit = selected_unit
            if channel not in data or unit not in data[channel]:
                return
            
            #psth_data = data[channel][unit]['psth_data']
            bins = data[channel][unit]['bins']
            smoothed_psth = data[channel][unit]['smoothed_psth']
            maxima_indices = data[channel][unit]['maxima_indices']
            minima_indices = data[channel][unit]['minima_indices']
            
            self.curve_axes.set_xscale('linear')
            if self.append_data_curve:
                self.curve_axes.plot(self.bins, smoothed_psth, self.data_point_styles[self.data_curves-1])
            elif not np.array_equal(self.bins,bins):
                self.make_chart(bins, smoothed_psth)
            else:
                self.curve_data.set_xdata(self.bins)
                self.curve_data.set_ydata(smoothed_psth)
            
            self.data_form.gen_curve_data(self.bins, smoothed_psth, maxima_indices, minima_indices)
            self.curve_axes.set_xlim(min(self.bins),max(self.bins))
            self.curve_axes.set_ylim(auto=True)
            #self.curve_axes.set_ylim(0,100)
            self.curve_axes.relim()
            self.curve_axes.autoscale_view(scalex=False, scaley=True)
            
        self.fig.canvas.draw()
    
    def on_update_data_timer(self, _event):
        if self.collecting_data and self.connected_to_server:
            self.update_data_thread = UpdateDataThread(self, self.psth_data)
            self.update_data_thread.start()
        
    def start_data(self):
        if self.psth_data is None:
            self.psth_data = TimeHistogram.PSTHAverage()
        self.collecting_data = True
        self.connected_to_server = True
    
    def stop_data(self):
        self.collecting_data = False
        self.clear_data()
        self.psth_data = None
        #if hasattr(self, 'update_data_thread') and self.psth_data is not None:
            #RenewDataThread(self, self.psth_data, self.update_data_thread).start()
        
    def restart_data(self):
        self.stop_data()
        self.start_data()
    
    def smooth_curve(self, checked):
        pass
    
    def open_file(self, path, callback=None):
        self.psth_data = TimeHistogram.PSTHAverage(path)
        data_thread = UpdateFileDataThread(self, self.psth_data, callback)
        data_thread.start()
        self.connected_to_server = False
    
    def append_data(self, path, callback=None):
        self.append_data_curve = True
        self.data_curves += 1
        self.open_file(path, callback)
        
    def clear_data(self):
        self.append_data_curve = False
        self.data_curves = 1
        self.make_chart()
        wx.FindWindowByName('main_frame').unit_choice.clear_unit()
        self.data_form.clear_data()
    
    def save_data(self):
        data_dict = {}
        data_dict['data'] = self.data
        return data_dict
    
    def save_chart(self,path):
        self.canvas.print_figure(path, dpi=self.dpi)

class PSTHAverageFrame(MainFrame):
    """ The main frame of the application
    """
    def __init__(self):
        self.menu_view = None
        self.m_smooth = None
        super(PSTHAverageFrame, self).__init__('Peri-Stimulus Time Histogram(PSTH) Average')
    
    # invoked when MainFrame is initiated
    def create_menu(self):
        super(PSTHAverageFrame, self).create_menu()
        
        self.menu_view = wx.Menu()
        self.m_smooth = self.menu_view.AppendCheckItem(-1, "&Smooth Curve\tCtrl-S", "Smooth curve")
        self.menu_view.Check(self.m_smooth.GetId(), True)
        self.Bind(wx.EVT_MENU, self.on_check_smooth, self.m_smooth)
        
        self.menubar.Append(self.menu_view, "&View")
        self.SetMenuBar(self.menubar)

    def create_chart_panel(self):
        self.chart_panel = PSTHAveragePanel(self.panel, 'PSTH Chart')
    
    def on_data_updated(self, event):
        data = event.get_data()
        self.unit_choice.update_units(data)
        self.chart_panel.update_chart(data)
        
    def on_check_smooth(self, _event):
        if self.m_smooth.IsChecked():
            self.chart_panel.smooth_curve(True)
            self.flash_status_message("Smoothing curve data.")
        else:
            self.chart_panel.smooth_curve(False)
            self.flash_status_message("Curve data without smooth.")
        self.chart_panel.update_chart()
    
class RCPSTHAveragePanel(PSTHAveragePanel, RCPanel):
    def __init__(self, *args,**kwargs):
        PSTHAveragePanel.__init__(self,*args,**kwargs)
        RCPanel.__init__(self)
    
    def check_errbar(self, checked):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
        parent = wx.FindWindowByName('main_frame')
        parent.menu_view.Check(parent.m_smooth.GetId(), checked)
        evt.SetId(parent.m_smooth.GetId())
        wx.PostEvent(parent, evt)
    
    def get_data(self):
        return self.data_form.get_data()
    
    def export_chart(self, path):
        self.save_chart(path)

class PyroPSTHAverageFrame(PSTHAverageFrame):
    """
        Remote controlled PSTH frame
    """
    def __init__(self, pyro_port):
        self.pyro_port = pyro_port
        self.pyro_daemon = None
        self.PYRO_URI = None
        super(PyroPSTHAverageFrame, self).__init__()
        
    def create_chart_panel(self):
        self.chart_panel = RCPSTHAveragePanel(self.panel, 'PSTH Chart')
        threading.Thread(target=self.create_pyro_server).start()
        
    def create_pyro_server(self):
        Pyro.config.PYRO_MULTITHREADED = 0
        Pyro.core.initServer()
        pyro_port = self.pyro_port
        self.pyro_daemon = Pyro.core.Daemon(port=pyro_port)
        self.PYRO_URI = self.pyro_daemon.connect(self.chart_panel, 'psth_server')
        if self.pyro_daemon.port is not pyro_port:
            raise RuntimeError("Pyro daemon cannot run on port %d. " %pyro_port +
                               "Probably the port has already been taken up by another pyro daemon.")
        self.pyro_daemon.requestLoop()
    
    def on_exit(self, event):
        self.pyro_daemon.disconnect(self.chart_panel)
        self.pyro_daemon.shutdown()
        super(PyroPSTHAverageFrame, self).on_exit(event)
        