# Plot receptive field structure obtained by spike triggered average.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from __future__ import division
import wx
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas

from Experimenter.Data.Fitting import GaussFit,GaborFit
from Experimenter.GUI.DataCollect import UpdateDataThread,RestartDataThread
from Experimenter.GUI.DataCollect import MainFrame,adjust_spines
from Experimenter.ReverseCorrelation import RevCorr

class STAPanel(wx.Panel):
    """ Receptive field plot.
    """
    def __init__(self, parent, label, name='sta_panel'):
        super(STAPanel, self).__init__(parent, -1, name=name)
        
        self.interpolation_changed = False
        self.show_colorbar_changed = False
        self.collecting_data = False
        self.data_started = False
        self.connected_to_server = False
        self.showing_colorbar = True
        self.fitting_gaussian = False
        self.fitting_gabor = False
        # default data type
        self.sta_data = None
        self.stimulus = None
        # reverse time in ms
        time_slider = 85
        self.time = time_slider/1000
        
        self.dpi = 100
        self.fig = Figure((6.0, 6.0), dpi=self.dpi, facecolor='w')
        self.canvas = FigCanvas(self, -1, self.fig)
        self.fig.subplots_adjust(bottom=0.05, left=0.05, right=0.95, top=0.95)
        #
        self.slider = wx.Slider(self, -1, time_slider, 0, 200, None, (250, 50), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
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
        # slider
        vbox = wx.BoxSizer(wx.VERTICAL)
        option_hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        time_text = wx.StaticText(self, -1, 'Time:')
        option_hbox1.Add(time_text,0,wx.LEFT)
        option_hbox1.Add(self.slider,0,wx.LEFT)
        vbox.Add(option_hbox1,1,wx.TOP, 20)

        # canvas 
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.canvas, 0, flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        hbox.Add(vbox,flag=wx.TOP)
        
        sizer.Add(hbox, 0, wx.ALIGN_CENTRE)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(2000)
        self.Bind(wx.EVT_SLIDER, self.on_slider_update)
                
    def make_chart(self):
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        adjust_spines(self.axes,spines=[],spine_outward=[],xticks='none',yticks='none',tick_label=[])
        img = np.zeros((64,64,3))
        self.img_dim = img.shape
        self.im = self.axes.imshow(img,interpolation=self.interpolation)
        
    def set_data(self, data):
        self.data = data
    
    def update_chart(self,data=None):
        if data is None and hasattr(self, 'data'):
            data = self.data
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            img = self.sta_data.get_img(data, channel, unit, tau=self.time, format='rgb')
            if self.img_dim != img.shape or self.interpolation_changed or self.show_colorbar_changed:
                self.make_chart()
                self.im = self.axes.imshow(img,interpolation=self.interpolation)
                self.img_dim = img.shape
                self.interpolation_changed = False
                self.show_colorbar_changed = False
                if self.showing_colorbar:
                    self.fig.colorbar(self.im, shrink=1.0, fraction=0.045, pad=0.05, ticks=[0.0, 0.5, 1.0])
                #===============================================================
                # if isinstance(self.sta_data, RevCorr.STAData):
                #    cbar.ax.set_yticklabels(["off", " ", "on"])
                # if isinstance(self.sta_data, RevCorr.ParamMapData):
                #    cbar.ax.set_yticklabels([" ", " ", "response"])
                #===============================================================
            if self.fitting_gaussian or self.fitting_gabor:
                float_img = self.sta_data.get_img(data, channel, unit, tau=self.time, format='float')
                if self.fitting_gaussian:
                    _params,img = self.gauss_fitter.gaussfit2d(float_img,returnfitimage=True)
                elif self.fitting_gabor:
                    _params,img = self.gabor_fitter.gaborfit2d(float_img,returnfitimage=True)
                img = self.sta_data.float_to_rgb(img,cmap='jet')
            self.im.set_data(img)
            #self.axes.set_title(self.title)
            if isinstance(self.sta_data,RevCorr.STAData):
                self.stimulus = 'white_noise'
                wx.FindWindowByName('main_frame').SetTitle("Receptive field spatial map")
            if isinstance(self.sta_data,RevCorr.ParamMapData):
                self.stimulus = 'param_mapping'
                wx.FindWindowByName('main_frame').SetTitle("Parameters subspace map")
            self.im.autoscale()
            self.canvas.draw()
    
    def on_update_data_timer(self, event):
        if self.collecting_data and self.connected_to_server:
            self.update_data_thread = UpdateDataThread(self, self.sta_data)
    
    def start_data(self):
        if self.sta_data is None:
            self.sta_data = RevCorr.STAData()
        self.collecting_data = True
        self.data_started = True
        self.connected_to_server = True
    
    def stop_data(self):
        self.collecting_data = False
        self.data_started = False
        
    def restart_data(self):
        self.collecting_data = False
        self.make_chart()
        self.sta_data = RevCorr.STAData()
        if self.data_started and self.sta_data is not None:
            RestartDataThread(self, self.sta_data, self.update_data_thread)
        self.collecting_data = True
        self.data_started = True
           
    def sparse_noise_data(self):
        self.sta_data = RevCorr.STAData()
        self.restart_data()
    
    def param_mapping_data(self):
        self.sta_data = RevCorr.ParamMapData()
        self.restart_data()
            
    def gaussianfit(self, checked):
        self.gauss_fitter = GaussFit()
        self.fitting_gaussian = checked
        
    def gaborfit(self, checked):
        self.gabor_fitter = GaborFit()
        self.fitting_gabor = checked
        
    def show_colorbar(self, checked):
        self.show_colorbar_changed = True
        self.showing_colorbar = checked
        
    def on_show_popup(self, event):
        pos = event.GetPosition()
        pos = event.GetEventObject().ScreenToClient(pos)
        self.PopupMenu(self.popup_menu, pos)
    
    def on_slider_update(self, event):
        # reverse time in ms
        self.time = self.slider.GetValue() / 1000
        if hasattr(self, 'data'):
            self.update_chart(self.data)
        
    def on_interpolation_selected(self, event):
        item = self.interpolation_menu.FindItemById(event.GetId())
        interpolation = item.GetText()
        if interpolation != self.interpolation:
            self.interpolation_changed = True
        self.interpolation = interpolation
        if hasattr(self, 'data'):
            self.update_chart(self.data)
    
    def open_file(self, path):
        self.sta_data = RevCorr.STAData(path)
        UpdateDataThread(self, self.sta_data)
        self.connected_to_server = False
    
    def save_data(self):
        data_dict = {}
        data_dict['stimulus'] = self.stimulus
        data_dict['data'] = self.data
        return data_dict
        
    def save_chart(self, path):
        self.canvas.print_figure(path, dpi=self.dpi)

class STAFrame(MainFrame):
    """ The main frame of the application
    """
    def __init__(self):
        title = 'Spike Triggered Average(STA)'
        super(STAFrame, self).__init__(title)

    def create_menu(self):
        super(STAFrame, self).create_menu()
        
        menu_source = wx.Menu()
        m_sparse_noise = menu_source.AppendRadioItem(-1, "Sparse &Noise\tCtrl-N", "Sparse noise data")
        self.Bind(wx.EVT_MENU, self.on_sparse_noise_data, m_sparse_noise)
        m_param_mapping = menu_source.AppendRadioItem(-1, "Param &Mapping\tCtrl-M", "Parameter mapping data")
        self.Bind(wx.EVT_MENU, self.on_param_mapping_data, m_param_mapping)
        
        self.menu_fitting = wx.Menu()
        self.m_gaussfitter = self.menu_fitting.AppendCheckItem(-1, "Ga&ussian\tCtrl-U", "Gaussian fitting")
        self.menu_fitting.Check(self.m_gaussfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaussfitter, self.m_gaussfitter)
        self.m_gaborfitter = self.menu_fitting.AppendCheckItem(-1, "Ga&bor\tCtrl-B", "Gabor fitting")
        self.menu_fitting.Check(self.m_gaborfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaborfitter, self.m_gaborfitter)
        self.menu_uncheck_binds = {self.m_gaussfitter.GetId():self.uncheck_gaussfitter, self.m_gaborfitter.GetId():self.uncheck_gaborfitter} 
        
        self.menu_view = wx.Menu()
        self.m_colorbar = self.menu_view.AppendCheckItem(-1, "&Colorbar\tCtrl-C", "Display colorbar")
        self.menu_view.Check(self.m_colorbar.GetId(), True)
        self.Bind(wx.EVT_MENU, self.on_check_colorbar, self.m_colorbar)
        
        self.menubar.Append(menu_source, "&Source")
        self.menubar.Append(self.menu_fitting, "&Fitting")
        self.menubar.Append(self.menu_view, "&View")
        self.SetMenuBar(self.menubar)
    
    def create_chart_panel(self):
        self.chart_panel = STAPanel(self.panel, 'STA chart')
        
    def on_data_updated(self, event):
        data = event.get_data()
        self.chart_panel.set_data(data)
        self.unit_choice.update_units(data['spikes'])
        self.chart_panel.update_chart(data)
    
    def on_sparse_noise_data(self, event):
        self.chart_panel.sparse_noise_data()
        self.flash_status_message("Data source changed to sparse noise")
    
    def on_param_mapping_data(self, event):
        self.chart_panel.param_mapping_data()
        self.flash_status_message("Data source changed to parameter mapping")
        
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
    
    def on_check_colorbar(self, event):
        self.chart_panel.show_colorbar(self.m_colorbar.IsChecked())
        self.chart_panel.update_chart()

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = STAFrame()
    app.frame.Show()
    app.MainLoop()
