# Core gui elements for data analysis.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import numpy as np
import os
import time
import threading
import wx
import matplotlib
#from StimControl.LightStim.LightData import IndexedParam

class IndexedParam(list):
    def __init__(self,parameter):
        if parameter == 'orientation':
            super(IndexedParam, self).__init__(np.linspace(0.0, 360.0, 16, endpoint=False))
        elif parameter == 'orientation_180':
            super(IndexedParam, self).__init__(np.linspace(0.0, 180.0, 16, endpoint=False))
        elif parameter == 'spatial_freq':
            super(IndexedParam, self).__init__(np.linspace(0.05, 1.0, 16))
        elif parameter == 'phase_at_t0':
            super(IndexedParam, self).__init__(np.linspace(0.0, 360.0, 16, endpoint=False))
        elif parameter is None:
            super(IndexedParam, self).__init__([None])
        else:
            raise RuntimeError('Cannot understand parameter:%s' %str(parameter))

EVT_DATA_UPDATED_TYPE = wx.NewEventType()
EVT_DATA_UPDATED = wx.PyEventBinder(EVT_DATA_UPDATED_TYPE, 1)
EVT_DATA_RESTART_TYPE = wx.NewEventType()
EVT_DATA_RESTART = wx.PyEventBinder(EVT_DATA_RESTART_TYPE, 1)
EVT_UNIT_SELECTED_TYPE = wx.NewEventType()
EVT_UNIT_SELECTED = wx.PyEventBinder(EVT_UNIT_SELECTED_TYPE, 1)

class DataUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, data=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._data = data
    def get_data(self):
        return self._data

class UpdateDataThread(threading.Thread):
    def __init__(self, parent, source):
        threading.Thread.__init__(self)
        self._parent = parent
        self._source = source
        self.run()
    def run(self):
        updated_data = self._source.get_data()
        evt = DataUpdatedEvent(EVT_DATA_UPDATED_TYPE, -1, updated_data)
        wx.PostEvent(self._parent, evt)
            
class DataRestartEvent(wx.PyCommandEvent):
    pass

class CheckRestart(threading.Thread):
    def __init__(self, parent, source):
        threading.Thread.__init__(self)
        self._parent = parent
        self._source = source
        self.run()
    def run(self):
        if self._source.is_new_start():
            evt = DataRestartEvent(EVT_DATA_RESTART_TYPE, -1)
            wx.PostEvent(self._parent, evt)
            print "New data started."
            self._source.set_new_start(False)

class UnitSelectedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, unit):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._unit = unit
    def get_unit(self):
        return self._unit

class RestartDataThread(threading.Thread):
    def __init__(self, parent, source, update_data_thread):
        threading.Thread.__init__(self)
        self._parent = parent
        self._source = source
        self._update_data_thread = update_data_thread
        self.run()
    def run(self):
        # wait until the update data threat quits
        while self._update_data_thread.isAlive():
            time.sleep(0.1)
        self._source.renew_data()

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
        index = self.unit_list.GetSelection()
        unit = self.items[index]
        evt = UnitSelectedEvent(EVT_UNIT_SELECTED_TYPE, -1, unit)
        wx.PostEvent(self.GetParent(), evt)
        
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
        
class DataForm(wx.Panel):
    """ display results.
    """
    def __init__(self, parent, label, text_size=(100,600), name='results'):
        super(DataForm, self).__init__(parent, -1, name=name)
        
        self.results = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.HSCROLL | wx.VSCROLL | wx.TE_READONLY, size=text_size)        
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.results, 0, flag=wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def gen_curve_data(self, x, means, stds, fittings, model, label):
        if label[0] == 'orientation':
            label[0] = 'ori'
        elif label[0] == 'spatial_frequency':
            label[0] = 'spf'
        elif label[0] == 'phase':
            label[0] = 'pha'
        data = '-'*18 + '\nData:\n' + "\t".join(label) + '\n'
        for line in zip(x,means,stds):
            dataline = '\t'.join('%.1f' %value for value in line)
            data += dataline + '\n'
        extremes = ''
        if any(model):
            max_index = model.argmax()
            min_index = model.argmin()
            extremes += '\n' + '-'*18 + '\nMax/min values:\n'
            extremes += 'Max '+ label[1] + '\t' + label[0] + '\n'
            extremes += '%.1f\t%.1f\n' %(model[max_index], fittings[max_index])
            extremes += 'Min '+ label[1] + '\t' + label[0] + '\n'
            extremes += '%.1f\t%.1f\n' %(model[min_index], fittings[min_index])
        form = data + extremes
        self.results.SetValue(form)
        
    def gen_img_data(self,img,type):
        dims = img.shape
        data = ''
        extremes = ''
        if type == 'white_noise':
            pass
        elif type == 'param_mapping':
            ori = IndexedParam('orientation_180')
            spf = IndexedParam('spatial_freq')
            x_max,y_max = np.unravel_index(img.argmax(), dims)
            x_min,y_min = np.unravel_index(img.argmin(), dims)
            extremes += '\n' + '-'*18 + '\nMax/min values:\n'
            extremes += 'Max: ' + '\tori' + '\tspf\n'
            extremes += '\t%.1f\t%.1f\n' %(ori[x_max], spf[y_max])
            extremes += 'Min ' + '\tori' + '\tspf\n'
            extremes += '\t%.1f\t%.1f\n' %(ori[x_min], spf[y_min])
        form = data + extremes
        self.results.SetValue(form)

class MainFrame(wx.Frame):
    """ The main frame of the application
    """
    def __init__(self, title):
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        #style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, style=style, name='main_frame')

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.Bind(EVT_DATA_UPDATED, self.on_data_updated)
        self.Bind(EVT_DATA_RESTART, self.on_restart_data)
        self.Bind(EVT_UNIT_SELECTED, self.on_select_unit)
        
    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_open_file = menu_file.Append(-1, "&Open file\tCtrl-O", "Open Plexon PLX file")
        self.Bind(wx.EVT_MENU, self.on_open_file, m_open_file)
        m_connect_server = menu_file.Append(-1, "&Connect to server\tCtrl-C", "Connect to OmniPlex Server")
        self.Bind(wx.EVT_MENU, self.on_connect_server, m_connect_server)
        menu_file.AppendSeparator()
        m_expt_data = menu_file.Append(-1, "Save &data\tCtrl-D", "Save data to file")
        self.Bind(wx.EVT_MENU, self.on_save_data, m_expt_data)
        m_expt_plot = menu_file.Append(-1, "Save &plot\tCtrl-P", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_chart, m_expt_plot)
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

        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_data, "&Data")
        self.SetMenuBar(self.menubar)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar(name='status_bar')

    def create_main_panel(self):
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("White")

        self.unit_choice = UnitChoice(self.panel, 'Select Unit')
        self.create_chart_panel()
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.unit_choice, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP, border=5)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.chart_panel, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_TOP, border=5)
        #self.hbox.Add(self.results, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_TOP, border=5)
        
        self.vbox.Add(self.hbox, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.panel.Layout()
        
    def create_chart_panel(self):
        pass
    
    def update_chart(self):
        self.chart_panel.update_chart()
    
    def on_select_unit(self, event):
        unit = event.get_unit()
        self.chart_panel.update_chart()
        self.flash_status_message("Select unit: %s" %unit, flash_len_ms=1000)
    
    def on_connect_server(self, event):
        self.on_start_data(-1)
        self.SetTitle(self.title)
    
    def on_open_file(self, event):
        file_choices = "PLX (*.plx)|*.plx"
        dlg = wx.FileDialog(
            self,
            message="Open Plexon plx file...",
            wildcard=file_choices,
            style=wx.OPEN|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.flash_status_message("Opening file %s ..." % path, flash_len_ms=5000)
            self.chart_panel.open_file(path)
            self.SetTitle(self.title + ' - ' + os.path.basename(path))
    
    def on_save_data(self, event):
        file_choices = "PKL (*.pkl)|*.pkl"
        dlg = wx.FileDialog(
            self,
            message="Save data as...",
            wildcard=file_choices,
            style=wx.SAVE|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            import pickle
            pkl_file = dlg.GetPath()
            data_dict = self.chart_panel.save_data()
            with open(pkl_file, 'wb') as pkl_output:
                pickle.dump(data_dict, pkl_output)
            self.flash_status_message("Saved to %s" % pkl_file)
        
    def on_save_chart(self, event):
        file_choices = "PNG (*.png)|*.png"
        dlg = wx.FileDialog(
            self,
            message="Save chart as...",
            wildcard=file_choices,
            style=wx.SAVE|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.chart_panel.save_chart(path)
            self.flash_status_message("Saved to %s" % path)
    
    def on_exit(self, event):
        self.Destroy()

    def on_data_updated(self, event):
        pass

    def on_start_data(self, event):
        self.chart_panel.start_data()
        self.flash_status_message("Data collecting started")
    
    def on_stop_data(self, event):
        self.chart_panel.stop_data()
        self.flash_status_message("Data collecting stopped")
    
    def on_restart_data(self, event):
        self.chart_panel.restart_data()
        self.flash_status_message("Data collecting restarted")

    def set_results(self, results):
        self.results.set_results(results)
    
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