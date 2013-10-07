# Frame for peri-stimulus time histogram analysis.
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from __future__ import division
import wx
import scipy
import threading
import Pyro.core
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib import pylab

from ..DataProcessing.Fitting.Fitters import GaussFit,SinusoidFit,GaborFit
from ..SpikeData import TimeHistogram
from Base import UpdateDataThread,UpdateFileDataThread
from Base import MainFrame,DataPanel,RCPanel,adjust_spines

class PSTHTuningDataPanel(DataPanel):
    def gen_psth_data(self, channel_unit_data):
        index = max(channel_unit_data, key=lambda k: channel_unit_data[k]['mean'])
        psth_data = channel_unit_data[index]['smooth_psth']
        fft_data = abs(scipy.fft(psth_data))
        try:
            F1 = max(fft_data[1:len(psth_data)//2])*2.0/len(psth_data)
            F0 = fft_data[0]/len(psth_data)
            ratio = F1/F0
        except ZeroDivisionError:
            ratio = np.nan
        mod_ratio = ''
        mod_ratio += '\n' + '-'*18 + '\nF1/F0 :\n'
        mod_ratio += '%.2f\n' %ratio
        self.results.AppendText(mod_ratio)
        self.data['F1/F0'] = ratio
        
    def gen_curve_data(self, x, means, stds, bg_noise, mono_dom, mono_nod, 
                       fittings, model_fitting, model_xdata, label):
        if label[0] == 'orientation':
            label[0] = 'ori'
            x = x*180/np.pi
        elif label[0] == 'spatial_frequency':
            label[0] = 'spf'
        elif label[0] == 'phase':
            label[0] = 'pha'
        elif label[0] == 'disparity':
            label[0] = 'dsp'
            
        self.data['param'] = label[0]
        ###########################
        ##### data
        data = '-'*18 + '\nData:\n' + "\t".join(label) + '\n'
        for line in zip(x,means,stds):
            dataline = '\t'.join('%6.2f' %value for value in line)
            data += dataline + '\n'
        self.data['data'] = data
        self.data['x'] = x
        self.data['means'] = means
        self.data['stds'] = stds
        ###########################
        ###########################
        ##### extremes
        extremes = ''
        if any(model_fitting):
            max_index = model_fitting.argmax()
            min_index = model_fitting.argmin()
            max_value = model_fitting[max_index]
            min_value = model_fitting[min_index]
            max_param = fittings[max_index]
            min_param = fittings[min_index]
        else:
            max_index = means.argmax()
            min_index = means.argmin()
            max_value = means[max_index]
            min_value = means[min_index]
            max_param = x[max_index]
            min_param = x[min_index]
        extremes += '-'*18 + '\nMax/min '+label[1]+':\n'
        extremes += 'Max ' + '\t' + label[0] + '\n'
        extremes += '%.2f\t%.2f\n' %(max_value, max_param)
        extremes += 'Min ' + '\t' + label[0] + '\n'
        extremes += '%.2f\t%.2f\n' %(min_value, min_param)
        self.data['max_param'] = max_param
        self.data['max_value'] = max_value
        self.data['min_param'] = min_param
        self.data['min_value'] = min_value
        ###########################
        ###########################
        ##### BII/S2N
        BII = ''
        S2N = ''
        BGN = ''
        DOM = ''
        NOD = ''
        if any(model_fitting) and label[0] == 'dsp':
            bii_ratio = 2.0*(max(model_fitting)-min(model_fitting))/(max(model_fitting)+min(model_fitting))
            BII += '-'*18 + '\nBII :\n'
            BII += '%.2f\n' %bii_ratio
            noise = np.sqrt(np.sum((model_xdata-means)**2)/means.size)
            s2n_ratio = (max(model_fitting)-min(model_fitting))/noise
            S2N += '-'*18 + '\nS/N :\n'
            S2N += '%.2f\n' %s2n_ratio
            if bg_noise is not None:
                BGN += '-'*18 + '\nBGN :\n'
                BGN += '%.2f\n' %bg_noise
            if mono_dom is not None:
                DOM += '-'*18 + '\nDOM :\n'
                DOM += '%.2f\n' %mono_dom
            if mono_nod is not None:
                NOD += '-'*18 + '\nNOD :\n'
                NOD += '%.2f\n' %mono_nod
            
            self.data['BII'] = bii_ratio
            self.data['S/N'] = s2n_ratio
            self.data['BGN'] = bg_noise
            self.data['DOM'] = mono_dom
            self.data['NOD'] = mono_nod
        ############################
        
        form = data + extremes + BII + S2N + BGN + DOM + NOD
        self.results.SetValue(form)

class PSTHTuningPanel(wx.Panel):
    """ Bar charts of PSTH tuning and instant firing rate.
    """
    def __init__(self, parent, label, name='psth_panel'):
        super(PSTHTuningPanel, self).__init__(parent, -1, name=name)
        
        self.connected_to_server = True
        self.collecting_data = True
        self.show_errbar_changed = False
        self.show_fitting_changed = False
        self.showing_errbar = False
        
        self.log_fitting = False
        self.curve_fitting = None
        self.curve_fitter = None
        self.append_data_curve = False
        self.polar_chart = False
        
        self.hist_bins = []
        self.hist_patches = []
        self.data_curves = 1
        self.data_point_styles = ['g.','r.','b.']
        self.fitting_curve_styles = ['g-','r--','b-.']
        
        self.data = None
        self.psth_data = None
        self.start_data()
        self.raw_data = None
        
        self.parameter = None
        self.curve_data = None
        self.errbars = None
        self.curve_axes = None
        
        self.fitting_x = None
        self.fitting_y = None
        self.fitting_data = None
        
        self.x = None
        self.means = None
        self.stds = None
        self.mono_left_mean = None
        self.mono_left_std = None
        self.mono_right_mean = None
        self.mono_right_std = None
        self.bg_noise_mean = None
        self.mono_dom_mean = None
        self.mono_nod_mean = None
        
        self.update_data_thread = None
        
        self.gauss_fitter = None
        self.sinusoid_fitter = None
        self.gabor_fitter = None
        
        # layout sizer
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        # data form
        self.data_form = PSTHTuningDataPanel(self, 'Data form')
        
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

    def make_chart(self,data=np.zeros(1),bins=np.arange(10)+1,polar=False):
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
    
    def set_data(self, data):
        self.data = data
    
    def update_chart(self, data=None):
        if data is None and self.data is None:
            return
        elif data is None and self.data is not None:
            data = self.data
        
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit is not None:
            channel, unit = selected_unit
            zeroth_psth_data = None
            polar_dict = {'orientation':True, 'spatial_frequency':False, 'phase':False, 'disparity':False}
            self.parameter = self.psth_data.parameter
            if self.parameter in polar_dict:
                polar_chart = polar_dict[self.parameter]
            else:
                polar_chart = self.polar_chart
            # histogram
            for index in [i for i in data[channel][unit].iterkeys() if (not i&1 and i<16)]:
                patch_index = index // 2
                spike_times = data[channel][unit][index]['spikes']
                bins = data[channel][unit][index]['bins']
                psth_data = data[channel][unit][index]['psth_data']
                if index == 0:
                    zeroth_psth_data = psth_data
                _trials = data[channel][unit][index]['trials']
                self.show_fitting_changed = False
                if len(bins) != len(self.hist_bins[patch_index]) or self.show_errbar_changed or polar_chart != self.polar_chart:
                    self.make_chart(spike_times, bins, polar_chart)
                    self.show_errbar_changed = False
                    self.show_fitting_changed = False
                #else:
                for rect,h in zip(self.hist_patches[patch_index],psth_data):
                    rect.set_height(h)
            
            for index in data[channel][unit].iterkeys():
                mean = data[channel][unit][index]['mean']
                std = data[channel][unit][index]['std']
                if index == -1:
                    self.bg_noise_mean = mean
                    self.bg_noise_std = std
                elif index <= 15:
                    self.means[index] = mean
                    self.stds[index] = std
                elif index == 16:
                    self.mono_left_mean = mean
                    self.mono_left_std = std
                elif index == 17:
                    self.mono_right_mean = mean
                    self.mono_right_std = std
            
            self.curve_axes.set_xscale('linear')
            
            if self.parameter == 'orientation':
                self.log_fitting = False
                self.x = np.linspace(0.0, 360.0, 17)/180*np.pi
                self.curve_axes.set_title('Orientation Tuning Curve',fontsize=12)
                if zeroth_psth_data is not None:
                    for rect,h in zip(self.hist_patches[-1],zeroth_psth_data):
                        rect.set_height(h)
                self.means[-1] = self.means[0]
                self.stds[-1] = self.stds[0]
            if self.parameter == 'spatial_frequency':
                self.log_fitting = True
                self.x = np.logspace(-1.0,0.5,16)
                self.curve_axes.set_title('Spatial Frequency Tuning Curve',fontsize=12)
                self.curve_axes.set_xscale('log')
                self.means = self.means[:len(self.x)]
                self.stds = self.stds[:len(self.x)]
                adjust_spines(self.curve_axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=10,youtward=30,\
                              xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=5,xminor_auto_loc=2,yminor_auto_loc=2,xmajor_loc=[0.1,0.5,1.0,2.0])
            if self.parameter in ('disparity','phase'):
                self.log_fitting = False
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
                if self.mono_left_mean is not None and self.mono_right_mean is not None:
                    #annotate dominant eye activity
                    self.mono_dom_mean = max(self.mono_left_mean, self.mono_right_mean)
                    self.curve_axes.annotate('', xy=(360, self.mono_dom_mean), xytext=(370, self.mono_dom_mean),
                                            arrowprops=dict(facecolor='black', frac=1.0, headwidth=10, shrink=0.05))
                    #annotate non-dominant eye activity
                    self.mono_nod_mean = min(self.mono_left_mean, self.mono_right_mean)
                    self.curve_axes.annotate('', xy=(360, self.mono_nod_mean), xytext=(370, self.mono_nod_mean),
                                            arrowprops=dict(facecolor='gray', frac=1.0, headwidth=10, shrink=0.05))
                if self.bg_noise_mean is not None:
                    #annotate background activity
                    self.curve_axes.annotate('', xy=(360, self.bg_noise_mean), xytext=(370, self.bg_noise_mean),
                                            arrowprops=dict(facecolor='white', frac=1.0, headwidth=10, shrink=0.05))
                    
                adjust_spines(self.curve_axes,spines=['left','bottom','right'],spine_outward=['left','right','bottom'],xoutward=10,youtward=30,\
                              xticks='bottom',yticks='both',tick_label=['x','y'],xaxis_loc=5,xminor_auto_loc=2,yminor_auto_loc=2)
            
            if self.append_data_curve:
                self.curve_axes.plot(self.x, self.means, self.data_point_styles[self.data_curves-1])
            else:
                self.curve_data.set_xdata(self.x)
                self.curve_data.set_ydata(self.means)
            if self.errbars is not None:
                self._update_errbars(self.errbars,self.x,self.means,self.stds)
            
            ##################################################################
            ##### Curve Fitting
            ##################################################################
            if self.log_fitting:
                self.fitting_x = np.logspace(np.log10(self.x[0]), np.log10(self.x[-1]), self.fitting_x.size, endpoint=True)
            else:
                self.fitting_x = np.linspace(self.x[0], self.x[-1], self.fitting_x.size, endpoint=True)
            
            model_fitting = np.zeros(self.fitting_x.size)
            model_xdata = np.zeros(self.x.size)
            nonzero = np.nonzero(self.means)[0]
            if self.curve_fitting == 'gauss':
                if self.log_fitting:
                    model_xdata,model_fitting = self.curve_fitter.loggaussfit1d(self.x[nonzero], self.means[nonzero], self.fitting_x)
                else:
                    model_xdata,model_fitting = self.curve_fitter.gaussfit1d(self.x[nonzero], self.means[nonzero], self.fitting_x)
            elif self.curve_fitting == 'sin':
                model_xdata,model_fitting = self.curve_fitter.sinusoid1d(self.x[nonzero], self.means[nonzero], self.fitting_x)
            elif self.curve_fitting == 'gabor':
                model_xdata,model_fitting = self.curve_fitter.gaborfit1d(self.x[nonzero], self.means[nonzero], self.fitting_x)
                
            if self.append_data_curve:
                self.curve_axes.plot(self.fitting_x, model_fitting, self.fitting_curve_styles[self.data_curves-1])
            else:
                self.fitting_data.set_xdata(self.fitting_x)
                self.fitting_data.set_ydata(model_fitting)
                
            label = [self.parameter, 'rate', 'std']
            self.data_form.gen_curve_data(self.x, self.means, self.stds,
                                          self.bg_noise_mean, self.mono_dom_mean, self.mono_nod_mean,
                                          self.fitting_x, model_fitting, model_xdata, label)
            if self.parameter == 'orientation':
                self.data_form.gen_psth_data(data[channel][unit])
            self.curve_axes.set_xlim(min(self.x),max(self.x))
            self.curve_axes.set_ylim(min(0, min(self.means)), (max(self.means)*1.2)//10*10)
            #self.curve_axes.set_ylim(auto=True)
            self.curve_axes.relim()
            self.curve_axes.autoscale_view(scalex=False, scaley=False)
                
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
    
    def on_update_data_timer(self, _event):
        if self.collecting_data and self.connected_to_server:
            self.update_data_thread = UpdateDataThread(self, self.psth_data)
            self.update_data_thread.start()
        
    def start_data(self):
        if self.psth_data is None:
            self.psth_data = TimeHistogram.PSTHTuning()
        self.collecting_data = True
        self.connected_to_server = True
    
    def stop_data(self):
        self.collecting_data = False
        self.clear_data()
        self.psth_data = None
        
    def restart_data(self):
        self.stop_data()
        self.start_data()
        
    def choose_fitting(self, fitting):
        if fitting == 'none':
            self.curve_fitting = None
            self.curve_fitter = None
        if fitting == 'gauss':
            self.curve_fitting = 'gauss'
            self.curve_fitter = GaussFit()
        if fitting == 'sin':
            self.curve_fitting = 'sin'
            self.curve_fitter = SinusoidFit()
        if fitting == 'gabor':
            self.curve_fitting = 'gabor'
            self.curve_fitter = GaborFit()
    
    def show_errbar(self, checked):
        self.show_errbar_changed = True
        self.showing_errbar = checked
    
    def open_file(self, path, callback=None):
        self.psth_data = TimeHistogram.PSTHTuning(path)
        data_thread = UpdateFileDataThread(self, self.psth_data, callback)
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
        data_dict['stimulus'] = self.psth_data.parameter
        data_dict['x'] = self.x
        data_dict['y'] = self.means
        data_dict['data'] = self.data
        return data_dict
    
    def save_chart(self,path):
        self.canvas.print_figure(path, dpi=self.dpi)

class PSTHTuningFrame(MainFrame):
    """ The main frame of the application
    """
    def __init__(self):
        self.menu_fitting = None
        self.m_nonefitter = None
        self.m_gaussfitter = None
        self.m_sinfitter = None
        self.m_gaborfitter = None
        self.menu_uncheck_binds = None
        self.menu_view = None
        self.m_errbar = None
        super(PSTHTuningFrame, self).__init__('Peri-Stimulus Time Histogram(PSTH) Tuning')
    
    # invoked when MainFrame is initiated
    def create_menu(self):
        super(PSTHTuningFrame, self).create_menu()
        
        self.menu_fitting = wx.Menu()
        self.m_nonefitter = self.menu_fitting.AppendRadioItem(-1, "&None\tCtrl-N", "No fitting")
        self.menu_fitting.Check(self.m_nonefitter.GetId(), True)
        self.Bind(wx.EVT_MENU, self.on_check_nonefitter, self.m_nonefitter)
        self.m_gaussfitter = self.menu_fitting.AppendRadioItem(-1, "Ga&ussian\tCtrl-U", "Gaussian curve")
        self.menu_fitting.Check(self.m_gaussfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaussfitter, self.m_gaussfitter)
        self.m_sinfitter = self.menu_fitting.AppendRadioItem(-1, "&Sinusoidal\tCtrl-S", "Sinusoidal curve")
        self.menu_fitting.Check(self.m_sinfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_sinfitter, self.m_sinfitter)
        self.m_gaborfitter = self.menu_fitting.AppendRadioItem(-1, "Ga&bor\tCtrl-B", "Gabor curve")
        self.menu_fitting.Check(self.m_gaborfitter.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_gaborfitter, self.m_gaborfitter)
        
        self.menu_view = wx.Menu()
        self.m_errbar = self.menu_view.AppendCheckItem(-1, "&Errorbar\tCtrl-E", "Display errorbar")
        self.menu_view.Check(self.m_errbar.GetId(), False)
        self.Bind(wx.EVT_MENU, self.on_check_errbar, self.m_errbar)
        
        self.menubar.Append(self.menu_fitting, "&Fitting")
        self.menubar.Append(self.menu_view, "&View")
        self.SetMenuBar(self.menubar)
        
    def create_chart_panel(self):
        self.chart_panel = PSTHTuningPanel(self.panel, 'PSTH Chart')
    
    def on_data_updated(self, event):
        data = event.get_data()
        self.unit_choice.update_units(data)
        self.chart_panel.set_data(data)
        self.chart_panel.update_chart(data)
    
    def on_check_nonefitter(self, _event):
        self.flash_status_message("Using no fitting")
        self.chart_panel.choose_fitting("none")
        self.chart_panel.update_chart()
        
    def on_check_gaussfitter(self, _event):
        self.flash_status_message("Using gaussian fitting")
        self.chart_panel.choose_fitting("gauss")
        self.chart_panel.update_chart()
        
    def on_check_sinfitter(self, _event):
        self.flash_status_message("Using sinusoidal fitting")
        self.chart_panel.choose_fitting("sin")
        self.chart_panel.update_chart()
        
    def on_check_gaborfitter(self, _event):
        self.flash_status_message("Using gabor fitting")
        self.chart_panel.choose_fitting("gabor")
        self.chart_panel.update_chart()
        
    def on_check_errbar(self, _event):
        if self.m_errbar.IsChecked():
            self.chart_panel.show_errbar(True)
            self.flash_status_message("Showing error bar")
        else:
            self.chart_panel.show_errbar(False)
            self.flash_status_message("Stoped showing error bar")
        self.chart_panel.update_chart()
    
class RCPSTHTuningPanel(PSTHTuningPanel, RCPanel):
    def __init__(self, *args,**kwargs):
        PSTHTuningPanel.__init__(self,*args,**kwargs)
        RCPanel.__init__(self)
            
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
        if fitting == 'sin':
            parent.menu_fitting.Check(parent.m_sinfitter.GetId(), True)
            evt.SetId(parent.m_sinfitter.GetId()) 
            wx.PostEvent(parent, evt)
        if fitting == 'gabor':
            parent.menu_fitting.Check(parent.m_gaborfitter.GetId(), True)
            evt.SetId(parent.m_gaborfitter.GetId()) 
            wx.PostEvent(parent, evt)
        
    def check_errbar(self, checked):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED)
        parent = wx.FindWindowByName('main_frame')
        parent.menu_view.Check(parent.m_errbar.GetId(), checked)
        evt.SetId(parent.m_errbar.GetId())
        wx.PostEvent(parent, evt)
        
    def get_data(self):
        return self.data_form.get_data()
        
class PyroPSTHTuningFrame(PSTHTuningFrame):
    """
        Remote controlled PSTH frame
    """
    def __init__(self, pyro_port):
        self.pyro_port = pyro_port
        self.pyro_daemon = None
        self.PYRO_URI = None
        super(PyroPSTHTuningFrame, self).__init__()
        
    def create_chart_panel(self):
        self.chart_panel = RCPSTHTuningPanel(self.panel, 'PSTH Chart')
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
        super(PyroPSTHTuningFrame, self).on_exit(event)
        