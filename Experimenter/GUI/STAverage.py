# Frame for spike-triggered average analysis.
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

from ..DataProcessing.Fitting.Fitters import GaussFit,GaborFit
from ..SpikeData import RevCorr,TimeHistogram
from Base import UpdateDataThread,UpdateFileDataThread
from Base import MainFrame,DataPanel,RCPanel,adjust_spines

EVT_TIME_UPDATED_TYPE = wx.NewEventType()
EVT_TIME_UPDATED = wx.PyEventBinder(EVT_TIME_UPDATED_TYPE, 1)

class TimeUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, time=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._time = time
    def get_time(self):
        return self._time

class OptionPanel(wx.Panel):
    """ display options.
    """
    def __init__(self, parent, label, time=85, name='options'):
        super(OptionPanel, self).__init__(parent, -1, name=name)
        self.time = time
        
        time_text = wx.StaticText(self, -1, 'Time:', style=wx.ALIGN_LEFT)
        self.slider = wx.Slider(self, -1, self.time, 0, 200, None, (250, 50), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.Bind(wx.EVT_SLIDER, self.on_slider_update)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(time_text, 0, flag=wx.ALL, border=5)
        sizer.Add(self.slider, 0, flag=wx.ALIGN_LEFT, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)
    def on_slider_update(self, _event):
        # reverse time in ms
        time = self.slider.GetValue() / 1000
        evt = TimeUpdatedEvent(EVT_TIME_UPDATED_TYPE, -1, time)
        wx.PostEvent(self.GetParent(), evt)
        
class STADataPanel(DataPanel):
    def gen_results(self,peak_time,params=None,img=None,data_type=None):
        class IndexedParam(list):
            def __init__(self,parameter):
                if parameter == 'orientation':
                    super(IndexedParam, self).__init__(np.linspace(0.0, 360.0, 16, endpoint=False))
                elif parameter == 'orientation_180':
                    super(IndexedParam, self).__init__(np.linspace(0.0, 180.0, 16, endpoint=False))
                elif parameter == 'spatial_freq':
                    super(IndexedParam, self).__init__(np.logspace(-1.0,0.5,16))
                elif parameter == 'phase_at_t0':
                    super(IndexedParam, self).__init__(np.linspace(0.0, 360.0, 16, endpoint=False))
                elif parameter is None:
                    super(IndexedParam, self).__init__([None])
                else:
                    raise RuntimeError('Cannot understand parameter:%s' %str(parameter))
        data = ''
        extremes = ''
        if peak_time is not None:
            self.data['peak_time'] = peak_time
            data += '-'*18 + '\nPeak time(ms):\n'
            data += '%.1f\n' %peak_time
        if data_type == 'white_noise':
            # img format: img[y_index][x_index]
            y_max,x_max = np.unravel_index(img.argmax(), img.shape)
            self.data['rf_center'] = (x_max,y_max)
            data += '-'*18 + '\nRF center:\n'
            data += 'Center position index(x,y):\n'
            data += '%.1f\t%.1f\n' %(x_max,y_max)
        elif data_type == 'param_mapping':
            ori = IndexedParam('orientation_180')
            spf = IndexedParam('spatial_freq')
            y_max,x_max = np.unravel_index(img.argmax(), img.shape)
            self.data['optimal_ori'] = ori[x_max]
            self.data['optimal_spf'] = spf[y_max]
            extremes += '\n' + '-'*18 + '\n'
            extremes += 'optimal ori: %.2f deg\n' %ori[x_max]
            extremes += 'optimal spf: %.2f cpd\n' %spf[y_max]
        form = data + extremes
        self.results.SetValue(form)

class STAPanel(wx.Panel):
    """ Receptive field plot.
    """
    def __init__(self, parent, label, name='sta_panel'):
        super(STAPanel, self).__init__(parent, -1, name=name)
        
        self.interpolation_changed = False
        self.show_colorbar_changed = False
        self.showing_colorbar = True
        self.image_fitting = None
        self.image_fitter = None
        
        # default data type
        self.collecting_data = True
        self.connected_to_server = True
        self.data = None
        self.sta_data = None
        self.psth_data = None
        self.data_type = None
        self.start_data()
        self.update_sta_data_thread = None
        self.update_psth_data_thread = None
        
        self.axes = None
        self.im = None
        self.img_dim = None
        
        self.gauss_fitter = None
        self.gabor_fitter = None
        
        self.peak_time = None
        # reverse time in ms
        time_slider = 85
        self.time = time_slider/1000
        
        self.dpi = 100
        self.fig = Figure((6.0, 6.0), dpi=self.dpi, facecolor='w')
        self.canvas = FigCanvas(self, -1, self.fig)
        self.fig.subplots_adjust(bottom=0.06, left=0.06, right=0.95, top=0.95)
        
        # popup menu of cavas
        interpolations = ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite', \
                               'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
        self.interpolation = 'nearest'
        self.interpolation_menu = wx.Menu()
        for interpolation in interpolations:
            item = self.interpolation_menu.AppendRadioItem(-1, interpolation)
            # check default interpolation
            if interpolation == self.interpolation:
                self.interpolation_menu.Check(item.GetId(), True)
            self.Bind(wx.EVT_MENU, self.on_interpolation_selected, item)
            wx.FindWindowByName('main_frame').Bind(wx.EVT_MENU, self.on_interpolation_selected, item)
        self.popup_menu = wx.Menu()
        self.popup_menu.AppendMenu(-1, '&Interpolation', self.interpolation_menu)
        self.canvas.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup)
        wx.FindWindowByName('main_frame').menu_view.AppendSubMenu(self.interpolation_menu, '&Interpolation')
        
        self.make_chart()
        
        #layout things
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        # options
        self.options = OptionPanel(self, 'Options', time=time_slider)
        self.Bind(EVT_TIME_UPDATED, self.on_update_time_slider)
        # results 
        self.data_form = STADataPanel(self, 'Results', text_size=(250,150))
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.options,1,wx.TOP|wx.CENTER, 0)
        vbox.Add(self.data_form,1,wx.TOP|wx.CENTER, 0)
        
        # canvas 
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.canvas, 0, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP, border=5)
        hbox.Add(vbox, 0, flag=wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_TOP, border=5)
        
        sizer.Add(hbox, 0, wx.ALIGN_CENTRE)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_sta_data_timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.on_update_sta_data_timer, self.update_sta_data_timer)
        self.update_sta_data_timer.Start(2000)
        
        self.update_psth_data_timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.on_update_psth_data_timer, self.update_psth_data_timer)
        self.update_psth_data_timer.Start(3000)
                
    def make_chart(self):
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        img = np.zeros((32,32,3))
        self.img_dim = img.shape
        self.im = self.axes.imshow(img,interpolation=self.interpolation)
        adjust_spines(self.axes,spines=['left','bottom'],spine_outward=[],
                      xticks='bottom',yticks='left',tick_label=['x','y'])
        self.axes.autoscale_view(scalex=True, scaley=True)
        self.fig.canvas.draw()
        
    def set_data(self, data):
        self.data = data
        
    def update_slider(self, data):
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            peak_time = data[channel][unit]['peak_time'] if channel in data and unit in data[channel] else None
            if peak_time is not None:
                self.peak_time = peak_time
                parent = wx.FindWindowByName('main_frame')
                parent.chart_panel.options.slider.SetValue(peak_time)
                evt = wx.CommandEvent(wx.wxEVT_COMMAND_SLIDER_UPDATED)
                evt.SetId(parent.chart_panel.options.slider.GetId())
                parent.chart_panel.options.on_slider_update(evt)
                wx.PostEvent(parent, evt)
    
    def update_chart(self,data=None):
        if data is None and self.data is None:
            return
        elif data is None and self.data is not None:
            data = self.data
        
        if isinstance(self.sta_data,RevCorr.STAData):
            self.data_type = 'white_noise'
        if isinstance(self.sta_data,RevCorr.ParamMapData):
            self.data_type = 'param_mapping'
        
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            img = self.sta_data.get_img(data, channel, unit, tau=self.time, img_format='rgb')
            if self.img_dim != img.shape or self.interpolation_changed or self.show_colorbar_changed:
                self.interpolation_changed = False
                self.show_colorbar_changed = False
                self.make_chart()
                self.im = self.axes.imshow(img,interpolation=self.interpolation)
                self.img_dim = img.shape
                                
                if self.showing_colorbar:
                    cbar = self.fig.colorbar(self.im, shrink=1.0, fraction=0.045, pad=0.05, ticks=[0, 0.5, 1])
                    if isinstance(self.sta_data, RevCorr.STAData):
                        cbar.set_ticklabels(["-1", "0", "1"])
                    if isinstance(self.sta_data, RevCorr.ParamMapData):
                        cbar.set_ticklabels(["0.0", "0.5", "1.0"])
                        
            self.data_form.gen_results(self.peak_time)
            
            if self.image_fitting is not None:
                float_img = self.sta_data.get_img(data, channel, unit, tau=self.time, img_format='float')
                if self.image_fitting == 'gauss':
                    params,img = self.image_fitter.gaussfit2d(float_img,returnfitimage=True)
                elif self.image_fitting == 'gabor':
                    params,img = self.image_fitter.gaborfit2d(float_img,returnfitimage=True)                
                self.data_form.gen_results(self.peak_time, params, img, self.data_type)
                img = self.sta_data.float_to_rgb(img,cmap='jet')
            
            self.im.set_data(img)
            #self.axes.set_title(self.title)
            self.im.autoscale()
            self.canvas.draw()
    
    def on_update_sta_data_timer(self, _event):
        if self.collecting_data and self.connected_to_server:
            self.update_sta_data_thread = UpdateDataThread(self, self.sta_data)
            self.update_sta_data_thread.start()
            
    def on_update_psth_data_timer(self, _event):
        if self.collecting_data and self.connected_to_server:
            self.update_psth_data_thread = UpdateDataThread(self, self.psth_data)
            self.update_psth_data_thread.start()
    
    def on_update_time_slider(self, event):
        self.time = event.get_time()
        self.update_chart()
        
    def start_data(self):
        data_type = wx.FindWindowByName('main_frame').get_data_type()
        if data_type == 'sparse_noise':
            self.sta_data = RevCorr.STAData()
        elif data_type == 'param_map':
            self.sta_data = RevCorr.ParamMapData()
        if self.psth_data is None:
            self.psth_data = TimeHistogram.PSTHAverage()
        self.collecting_data = True
        self.connected_to_server = True
    
    def stop_data(self):
        self.collecting_data = False
        self.clear_data()
        self.sta_data = None
        self.psth_data = None
        
    def restart_data(self):
        self.stop_data()
        self.start_data()
    
    def sparse_noise_data(self):
        self.sta_data = RevCorr.STAData()
        self.restart_data()
    
    def param_mapping_data(self):
        self.sta_data = RevCorr.ParamMapData()
        self.restart_data()
    
    def choose_fitting(self, fitting):
        if fitting == 'none':
            self.image_fitting = None
            self.image_fitter = None
        if fitting == 'gauss':
            self.image_fitting = 'gauss'
            self.image_fitter = GaussFit()
        if fitting == 'gabor':
            self.image_fitting = 'gabor'
            self.image_fitter = GaborFit()
        
    def show_colorbar(self, checked):
        self.show_colorbar_changed = True
        self.showing_colorbar = checked
        
    def on_show_popup(self, event):
        pos = event.GetPosition()
        pos = event.GetEventObject().ScreenToClient(pos)
        self.PopupMenu(self.popup_menu, pos)
        
    def on_interpolation_selected(self, event):
        item = self.interpolation_menu.FindItemById(event.GetId())
        interpolation = item.GetText()
        if interpolation != self.interpolation:
            self.interpolation_changed = True
        self.interpolation = interpolation
        if hasattr(self, 'data'):
            self.update_chart(self.data)
    
    def open_file(self, path, callback):
        data_type = wx.FindWindowByName('main_frame').get_data_type()
        if data_type == 'sparse_noise':
            self.sta_data = RevCorr.STAData(path)
        elif data_type == 'param_map':
            self.sta_data = RevCorr.ParamMapData(path)
        self.psth_data = TimeHistogram.PSTHAverage(path)
        UpdateFileDataThread(self, self.sta_data, callback).start()
        UpdateFileDataThread(self, self.psth_data, callback).start()
        self.connected_to_server = False
    
    def save_data(self):
        data_dict = {}
        data_dict['data_type'] = self.data_type
        data_dict['data'] = self.data
        return data_dict
        
    def save_chart(self, path):
        self.canvas.print_figure(path, dpi=self.dpi)
        
    def clear_data(self):
        self.data = None
        self.make_chart()
        wx.FindWindowByName('main_frame').unit_choice.clear_unit()
        self.data_form.clear_data()

class STAFrame(MainFrame):
    """ The main frame of the application
    """
    def __init__(self):
        self.menu_source = None
        self.m_sparse_noise = None
        self.m_param_mapping = None
        self.menu_fitting = None
        self.m_nonefitter = None
        self.m_gaussfitter = None
        self.m_gaborfitter = None
        self.menu_uncheck_binds = None
        self.menu_view = None
        self.m_colorbar = None
        super(STAFrame, self).__init__('Spike Triggered Average(STA)')
    
    # invoked when MainFrame is initiated
    def create_menu(self):
        super(STAFrame, self).create_menu()
        
        self.menu_source = wx.Menu()
        self.m_sparse_noise = self.menu_source.AppendRadioItem(-1, "Sparse &Noise\tCtrl-N", "Sparse noise data")
        self.Bind(wx.EVT_MENU, self.on_sparse_noise_data, self.m_sparse_noise)
        self.m_param_mapping = self.menu_source.AppendRadioItem(-1, "Param &Mapping\tCtrl-M", "Parameter mapping data")
        self.Bind(wx.EVT_MENU, self.on_param_mapping_data, self.m_param_mapping)
        
        self.menu_fitting = wx.Menu()
        self.m_nonefitter = self.menu_fitting.AppendRadioItem(-1, "&None\tCtrl-N", "No fitting")
        self.menu_fitting.Check(self.m_nonefitter.GetId(), True)
        self.Bind(wx.EVT_MENU, self.on_check_nonefitter, self.m_nonefitter)
        self.m_gaussfitter = self.menu_fitting.AppendRadioItem(-1, "Ga&ussian\tCtrl-U", "Gaussian fitting")
        self.menu_fitting.Check(self.m_gaussfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaussfitter, self.m_gaussfitter)
        self.m_gaborfitter = self.menu_fitting.AppendRadioItem(-1, "Ga&bor\tCtrl-B", "Gabor fitting")
        self.menu_fitting.Check(self.m_gaborfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaborfitter, self.m_gaborfitter)
        
        self.menu_view = wx.Menu()
        self.m_colorbar = self.menu_view.AppendCheckItem(-1, "&Colorbar\tCtrl-C", "Display colorbar")
        self.menu_view.Check(self.m_colorbar.GetId(), True)
        self.Bind(wx.EVT_MENU, self.on_check_colorbar, self.m_colorbar)
        
        self.menubar.Append(self.menu_source, "&Source")
        self.menubar.Append(self.menu_fitting, "&Fitting")
        self.menubar.Append(self.menu_view, "&View")
        self.SetMenuBar(self.menubar)
    
    def create_chart_panel(self):
        self.chart_panel = STAPanel(self.panel, 'STA chart')
        
    def on_data_updated(self, event):
        data_type = event.get_data_type()
        data = event.get_data()
        if data_type == 'psth_average':
            self.chart_panel.update_slider(data)
        else:
            self.chart_panel.set_data(data)
            self.unit_choice.update_units(data['spikes'])
            self.chart_panel.update_chart(data)
    
    def on_sparse_noise_data(self, _event):
        self.chart_panel.sparse_noise_data()
        self.flash_status_message("Data source changed to sparse noise")
    
    def on_param_mapping_data(self, _event):
        self.chart_panel.param_mapping_data()
        self.flash_status_message("Data source changed to parameter mapping")
        
    def get_data_type(self):
        if self.m_sparse_noise.IsChecked():
            return 'sparse_noise'
        elif self.m_param_mapping.IsChecked():
            return 'param_map'
        
    def on_check_nonefitter(self, _event):
        self.flash_status_message("Using no fitting")
        self.chart_panel.choose_fitting("none")
        self.chart_panel.update_chart()
        
    def on_check_gaussfitter(self, _event):
        self.flash_status_message("Using gaussian fitting")
        self.chart_panel.choose_fitting("gauss")
        self.chart_panel.update_chart()
        
    def on_check_gaborfitter(self, _event):
        self.flash_status_message("Using gabor fitting")
        self.chart_panel.choose_fitting("gabor")
        self.chart_panel.update_chart()
    
    def on_check_colorbar(self, _event):
        self.chart_panel.show_colorbar(self.m_colorbar.IsChecked())
        self.chart_panel.update_chart()
        
class RCSTAPanel(STAPanel, RCPanel):
    """
        Remote controlled PSTH panel
    """
    def __init__(self, *args,**kwargs):
        STAPanel.__init__(self,*args,**kwargs)
        RCPanel.__init__(self)
        
    def choose_source(self, source):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
        parent = wx.FindWindowByName('main_frame')
        if source == 'sparse_noise':
            parent.menu_source.Check(parent.m_sparse_noise.GetId(), True)
            evt.SetId(parent.m_sparse_noise.GetId())
            wx.PostEvent(parent, evt)
        if source == 'param_mapping':
            parent.menu_source.Check(parent.m_param_mapping.GetId(), True)
            evt.SetId(parent.m_param_mapping.GetId())
            wx.PostEvent(parent, evt)
        
    def check_fitting(self, fitting):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
        parent = wx.FindWindowByName('main_frame')
        if fitting == 'none':
            parent.menu_fitting.Check(parent.m_nonefitter.GetId(), True)
            evt.SetId(parent.m_nonefitter.GetId())
            wx.PostEvent(parent, evt)
        if fitting == 'gauss':
            parent.menu_fitting.Check(parent.m_gaussfitter.GetId(), True)
            evt.SetId(parent.m_gaussfitter.GetId())
            wx.PostEvent(parent, evt)
        if fitting == 'gabor':
            parent.menu_fitting.Check(parent.m_gaborfitter.GetId(), True)
            evt.SetId(parent.m_gaborfitter.GetId()) 
            wx.PostEvent(parent, evt)
        
    def check_colorbar(self, checked):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
        parent = wx.FindWindowByName('main_frame')
        parent.menu_view.Check(parent.m_colorbar.GetId(), checked)
        evt.SetId(parent.m_colorbar.GetId())
        wx.PostEvent(parent, evt)
    
    def set_latency(self, latency):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_SLIDER_UPDATED)
        parent = wx.FindWindowByName('main_frame')
        value = latency*1000
        parent.chart_panel.options.slider.SetValue(value)
        evt.SetId(parent.chart_panel.options.slider.GetId())
        wx.PostEvent(parent, evt)
    
    def get_data(self):
        return self.data_form.get_data()
    
    def export_chart(self, path):
        self.save_chart(path)

class PyroSTAFrame(STAFrame):
    """
        Remote controlled STA frame
    """
    def __init__(self, pyro_port):
        self.pyro_port = pyro_port
        self.pyro_daemon = None
        self.PYRO_URI = None
        super(PyroSTAFrame, self).__init__()

    def create_chart_panel(self):
        self.chart_panel = RCSTAPanel(self.panel, 'STA Chart')
        threading.Thread(target=self.create_pyro_server).start()
        
    def create_pyro_server(self):
        Pyro.config.PYRO_MULTITHREADED = 0
        Pyro.core.initServer()
        pyro_port = self.pyro_port
        self.pyro_daemon = Pyro.core.Daemon(port=pyro_port)
        self.PYRO_URI = self.pyro_daemon.connect(self.chart_panel, 'sta_server')
        if self.pyro_daemon.port is not pyro_port:
            raise RuntimeError("Pyro daemon cannot run on port %d. " %pyro_port +
                               "Probably the port has already been taken up by another pyro daemon.")
        self.pyro_daemon.requestLoop()
    
    def on_exit(self, event):
        self.pyro_daemon.disconnect(self.chart_panel)
        self.pyro_daemon.shutdown()
        super(PyroSTAFrame, self).on_exit(event)
        
        