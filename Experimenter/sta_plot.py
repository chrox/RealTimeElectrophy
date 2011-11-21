# Plot receptive field structure obtained by spike triggered average.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.
from __future__ import division
import os
import time
import wx
import numpy as np
import threading
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas

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
        
class RestartDataThread(threading.Thread):
    def __init__(self, parent, sta_data, update_data_thread):
        threading.Thread.__init__(self)
        self._parent = parent
        self._sta_data = sta_data
        self._update_data_thread = update_data_thread
        self.run()
    def run(self):
        # wait until the update data threat quits
        while self._update_data_thread.isAlive():
            time.sleep(0.1)
        self._sta_data.renew_data()
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
        if selected_unit in self.units:                         # selected unit previously
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
    def __init__(self, parent, label, name='sta_panel'):
        super(STAPanel, self).__init__(parent, -1, name=name)
        
        self.interpolation_changed = False
        self.show_colorbar_changed = False
        self.collecting_data = True
        self.data_started = False
        self.show_colorbar = True
        # default data type
        self.sta_data = RevCorr.STAData()

        # reverse time in ms
        time_slider = 85
        self.time = time_slider/1000
        
        self.dpi = 90
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
            self.Bind(wx.EVT_MENU, self.on_interpolation_selected, item)
        self.popup_menu = wx.Menu()
        self.popup_menu.AppendMenu(-1, '&Interpolation', self.interpolation_menu)
        self.canvas.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup)
        
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
        sizer.AddSpacer(30)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.update_data_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_data_timer, self.update_data_timer)
        self.update_data_timer.Start(2000)
        self.Bind(wx.EVT_SLIDER, self.on_slider_update)
                
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
            
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        adjust_spines(self.axes,spines=[],spine_outward=[],xticks='none',yticks='none',tick_label=[])
        img = np.zeros((64,64,3))
        self.img_dim = img.shape
        self.im = self.axes.imshow(img,interpolation=self.interpolation)
        
    def set_data(self, data):
        self.data = data
    
    def update_chart(self,data):
        selected_unit = wx.FindWindowByName('unit_choice').get_selected_unit()
        if selected_unit:
            channel, unit = selected_unit
            img = self.sta_data.get_rgb_img(data, channel, unit, tau=self.time)
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
            else:
                self.im.set_data(img)
            #self.axes.set_title(self.title)
            self.im.autoscale()
            self.canvas.draw()
    
    def on_update_data_timer(self, event):
        if self.collecting_data:
            self.update_data_thread = UpdateDataThread(self, self.sta_data)
    
    def start_data(self):
        self.collecting_data = True
        self.data_started = True
    
    def stop_data(self):
        self.collecting_data = False
        self.data_started = False
        
    def restart_data(self):
        self.collecting_data = False
        self.make_chart()
        if self.data_started:
            RestartDataThread(self, self.sta_data, self.update_data_thread)
        self.collecting_data = True
        self.data_started = True
           
    def sparse_noise_data(self):
        self.sta_data = RevCorr.STAData()
        wx.FindWindowByName('main_frame').SetTitle("Receptive field spatial map")
        self.restart_data()
    
    def param_mapping_data(self):
        self.sta_data = RevCorr.ParamMapData()
        wx.FindWindowByName('main_frame').SetTitle("Parameters subspace map")
        self.restart_data()
        
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
        
    def on_interpolation_selected(self, event):
        item = self.interpolation_menu.FindItemById(event.GetId())
        interpolation = item.GetText()
        if interpolation != self.interpolation:
            self.interpolation_changed = True
        self.interpolation = interpolation
        if hasattr(self, 'data'):
            self.update_chart(self.data)
        
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
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        #style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, style=style, name='main_frame')

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
        
        menu_data = wx.Menu()
        m_start = menu_data.Append(-1, "&Start\tCtrl-S", "Start data collecting")
        self.Bind(wx.EVT_MENU, self.on_start_data, m_start)
        m_stop = menu_data.Append(-1, "S&top\tCtrl-T", "Stop data collecting")
        self.Bind(wx.EVT_MENU, self.on_stop_data, m_stop)
        menu_data.AppendSeparator()
        m_restart = menu_data.Append(-1, "&Restart\tCtrl-R", "Restart data collecting")
        self.Bind(wx.EVT_MENU, self.on_restart_data, m_restart)
        
        menu_source = wx.Menu()
        m_sparse_noise = menu_source.AppendRadioItem(-1, "Sparse &Noise\tCtrl-N", "Sparse noise data")
        self.Bind(wx.EVT_MENU, self.on_sparse_noise_data, m_sparse_noise)
        m_param_mapping = menu_source.AppendRadioItem(-1, "Param &Mapping\tCtrl-M", "Parameter mapping data")
        self.Bind(wx.EVT_MENU, self.on_param_mapping_data, m_param_mapping)
        
        menu_view = wx.Menu()
        self.m_colorbar = menu_view.AppendCheckItem(-1, "&Colorbar\tCtrl-C", "Display colorbar")
        menu_view.Check(self.m_colorbar.GetId(), True)
        self.Bind(wx.EVT_MENU, self.on_check_colorbar, self.m_colorbar)
        
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_data, "&Data")
        self.menubar.Append(menu_source, "&Source")
        self.menubar.Append(menu_view, "&View")
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
        
    def on_data_updated(self, event):
        data = event.get_data()
        self.sta_chart.set_data(data)
        self.sta_chart.update_chart(data)
        self.unit_choice.update_units(data['spikes'])

    def on_save_chart(self, event):
        self.sta_chart.on_save_chart(event)
        
    def on_exit(self, event):
        self.Destroy()

    def on_start_data(self, event):
        self.sta_chart.start_data()
        self.flash_status_message("Data collecting started")
    
    def on_stop_data(self, event):
        self.sta_chart.stop_data()
        self.flash_status_message("Data collecting stopped")
    
    def on_restart_data(self, event):
        self.sta_chart.restart_data()
        self.flash_status_message("Data collecting restarted")
    
    def on_sparse_noise_data(self, event):
        self.sta_chart.sparse_noise_data()
        self.flash_status_message("Data source changed to sparse noise")
    
    def on_param_mapping_data(self, event):
        self.sta_chart.param_mapping_data()
        self.flash_status_message("Data source changed to parameter mapping")
        
    def on_check_colorbar(self, event):
        self.sta_chart.show_colorbar(self.m_colorbar.IsChecked())

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
