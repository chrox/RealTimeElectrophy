# Core gui elements for data analysis.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import os
import wx
import time
import Pyro.core
import threading
import matplotlib

EVT_DATA_UPDATED_TYPE = wx.NewEventType()
EVT_DATA_UPDATED = wx.PyEventBinder(EVT_DATA_UPDATED_TYPE, 1)
EVT_DATA_START_TYPE = wx.NewEventType()
EVT_DATA_START = wx.PyEventBinder(EVT_DATA_START_TYPE, 1)
EVT_DATA_STOP_TYPE = wx.NewEventType()
EVT_DATA_STOP = wx.PyEventBinder(EVT_DATA_STOP_TYPE, 1)
EVT_DATA_RESTART_TYPE = wx.NewEventType()
EVT_DATA_RESTART = wx.PyEventBinder(EVT_DATA_RESTART_TYPE, 1)
EVT_EXPORT_CHART_TYPE = wx.NewEventType()
EVT_EXPORT_CHART = wx.PyEventBinder(EVT_EXPORT_CHART_TYPE, 1)
EVT_UNIT_SELECTED_TYPE = wx.NewEventType()
EVT_UNIT_SELECTED = wx.PyEventBinder(EVT_UNIT_SELECTED_TYPE, 1)
EVT_PROG_BAR_HIDE_TYPE = wx.NewEventType()
EVT_PROG_BAR_HIDE = wx.PyEventBinder(EVT_PROG_BAR_HIDE_TYPE, 1)
EVT_PROG_BAR_SHOW_TYPE = wx.NewEventType()
EVT_PROG_BAR_SHOW = wx.PyEventBinder(EVT_PROG_BAR_SHOW_TYPE, 1)
EVT_FRAME_CLOSE_TYPE = wx.NewEventType()
EVT_FRAME_CLOSE = wx.PyEventBinder(EVT_FRAME_CLOSE_TYPE, 1)

class DataUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, data=None, data_type=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._data = data
        self._data_type = data_type
    def get_data(self):
        return self._data
    def get_data_type(self):
        return self._data_type

class ExportChartEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, path):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._path = path
    def get_path(self):
        return self._path

class UpdateDataThread(threading.Thread):
    def __init__(self, parent, source):
        threading.Thread.__init__(self)
        self._parent = parent
        self._source = source
        
    def run(self):
        updated_data = self._source.get_data()
        updated_data_type = self._source.get_data_type()
        evt = DataUpdatedEvent(EVT_DATA_UPDATED_TYPE, -1, updated_data, updated_data_type)
        wx.PostEvent(self._parent, evt)

class UpdateFileDataThread(UpdateDataThread):
    def __init__(self, parent, source, callback=None):
        super(UpdateFileDataThread,self).__init__(parent,source)
        self._callback = callback
        
    def run(self):
        updated_data = self._source.get_data(self._callback)
        updated_data_type = self._source.get_data_type()
        evt = DataUpdatedEvent(EVT_DATA_UPDATED_TYPE, -1, updated_data, updated_data_type)
        wx.PostEvent(self._parent, evt)

class UnitSelectedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, unit):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._unit = unit
    def get_unit(self):
        return self._unit

class RenewDataThread(threading.Thread):
    def __init__(self, parent, source, update_data_thread):
        threading.Thread.__init__(self)
        self._parent = parent
        self._source = source
        self._update_data_thread = update_data_thread

    def run(self):
        # wait until the update data threat quits
        while self._update_data_thread.isAlive():
            time.sleep(0.1)
        self._source.renew_data()

class HideProgressBarEvent(wx.PyCommandEvent):
    pass

class ShowProgressBarEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, percentage,done_size,file_size):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._percentage = percentage
        self._done_size = done_size
        self._file_size = file_size
    def get_percentage(self):
        return self._percentage
    def get_done_size(self):
        return self._done_size
    def get_file_size(self):
        return self._file_size

class UnitChoice(wx.Panel):
    """ A listbox of available channels and units.
    """
    def __init__(self, parent, label, name='unit_choice'):
        super(UnitChoice, self).__init__(parent, -1, name=name)
        self.units = None
        self.items = None

        self.unit_list = wx.ListBox(parent=self, size=(100,600))
        self.unit_list.Bind(wx.EVT_LISTBOX, self.on_select, self.unit_list)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.unit_list, 0, flag=wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def clear_unit(self):
        self.unit_list.SetItems([])
    
    def on_select(self,_event):
        index = self.unit_list.GetSelection()
        try:
            unit = self.items[index]
        except IndexError:
            pass
        else:
            evt = UnitSelectedEvent(EVT_UNIT_SELECTED_TYPE, -1, unit)
            wx.PostEvent(self.GetParent(), evt)
        
    def update_units(self,data):
        selected_unit = self.get_selected_unit()
        self.units = [(channel,unit) for channel in sorted(data.iterkeys(),key=int) for unit in sorted(data[channel].iterkeys())]
        self.items = ['DSP%d%c' %(channel,unit) for channel,unit in self.units]
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
        
class DataPanel(wx.Panel):
    """ display results.
    """
    def __init__(self, parent, label, text_size=(150,600), name='results'):
        super(DataPanel, self).__init__(parent, -1, name=name)
        
        self.results = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.HSCROLL | wx.VSCROLL | wx.TE_READONLY, size=text_size)        
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(self.results, 0, flag=wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)
        
        self.data = {}
        
    def clear_data(self):
        self.results.SetValue('')
        
    def get_data(self):
        return self.data

class MainFrame(wx.Frame):
    """ The main frame of the application
    """
    def __init__(self, title):
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX
        #style = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, title=title, style=style, name='main_frame')
        self.menubar = None
        self.statusbar = None
        self.progress_bar = None
        
        self.datetime_timer = None
        self.prog_bar_hide_timer = None
        self.status_msg_offtimer = None
        
        self.panel = None
        self.unit_choice = None
        
        self.opened_file = None
        self.currentOpenDir = ''
        self.currentSaveDir = ''
        self.title = title
        
        self.chart_panel = None
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.Bind(EVT_DATA_UPDATED, self.on_data_updated)
        self.Bind(EVT_DATA_START, self.on_start_data)
        self.Bind(EVT_DATA_STOP, self.on_stop_data)
        self.Bind(EVT_DATA_RESTART, self.on_restart_data)
        self.Bind(EVT_UNIT_SELECTED, self.on_select_unit)
        self.Bind(EVT_FRAME_CLOSE, self.on_exit)
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        
    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_open_file = menu_file.Append(-1, "&Open file\tCtrl-O", "Open Plexon PLX file")
        self.Bind(wx.EVT_MENU, self.on_open_file, m_open_file)
        m_append_data = menu_file.Append(-1, "&Append data\tCtrl-A", "Append data curve")
        self.Bind(wx.EVT_MENU, self.on_append_data, m_append_data)
        m_clear_data = menu_file.Append(-1, "Clea&r data\tCtrl-R", "Clear data plot")
        self.Bind(wx.EVT_MENU, self.on_clear_data, m_clear_data)
        menu_file.AppendSeparator()
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
        self.statusbar.SetFieldsCount(4) 
        self.statusbar.SetStatusWidths([-6, -2, -1, 145])
        self.progress_bar = wx.Gauge(self.statusbar, -1, 100, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.progress_bar.Hide()
        
        self.Bind(EVT_PROG_BAR_SHOW, self.progress_bar_on_show)
        self.Bind(EVT_PROG_BAR_HIDE, self.progress_bar_on_hide)
        self.Bind(EVT_PROG_BAR_SHOW, self.status_bar_on_update)
        
        wx.EVT_SIZE(self.statusbar, self.status_bar_on_size)
        self.datetime_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.status_bar_on_timer, self.datetime_timer)
        self.datetime_timer.Start(1000)

    def status_bar_on_size(self,_evt):
        rect = self.statusbar.GetFieldRect(1) 
        self.progress_bar.SetPosition((rect.x+2, rect.y+2)) 
        self.progress_bar.SetSize((rect.width-4, rect.height-4))
    
    def status_bar_on_timer(self,_evt):
        t = time.localtime(time.time())
        st = time.strftime("%a %b %d %H:%M:%S", t)
        self.statusbar.SetStatusText(st,3)
    
    def progress_bar_on_update(self,percentage,done_size,file_size,_elapsed_time,_left_time):
        wx.PostEvent(self, ShowProgressBarEvent(EVT_PROG_BAR_SHOW_TYPE,-1,percentage,done_size,file_size))
        if percentage == 1.0: 
            wx.PostEvent(self, HideProgressBarEvent(EVT_PROG_BAR_HIDE_TYPE,-1))
            
    def progress_bar_on_show(self,evt):
        percentage = evt.get_percentage()
        evt.Skip()
        self.progress_bar.Show()
        self.progress_bar.SetValue(int(percentage*100))
    
    def progress_bar_on_hide(self,_evt):
        self.prog_bar_hide_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,
                  lambda evt: self.progress_bar.Hide(),
                  self.prog_bar_hide_timer)
        self.prog_bar_hide_timer.Start(500, oneShot=True)
        
    def status_bar_on_update(self,evt):
        done_size = evt.get_done_size()
        file_size = evt.get_file_size()
        evt.Skip()
        self.statusbar.SetStatusText("%4.1f/%4.1f MB" %(done_size,file_size), 2)
    
    def create_main_panel(self):
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("White")

        self.unit_choice = UnitChoice(self.panel, 'Select Unit')
        self.create_chart_panel()
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox.AddSpacer(5)
        hbox.Add(self.unit_choice, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP, border=5)
        #self.hbox.AddSpacer(5)
        hbox.Add(self.chart_panel, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_TOP, border=5)
        #self.hbox.Add(self.results, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_TOP, border=5)
        
        vbox.Add(hbox, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.panel.Layout()
        
    def create_chart_panel(self):
        pass
    
    def update_chart(self):
        self.chart_panel.update_chart()
    
    def on_select_unit(self, event):
        unit = event.get_unit()
        self.chart_panel.update_chart()
        self.flash_status_message("Select unit: %s" %unit, flash_len_ms=1000)
    
    def on_connect_server(self, _event):
        self.on_start_data(-1)
        self.SetTitle(self.title)
    
    def on_open_file(self, _event):
        file_choices = "PLX (*.plx)|*.plx"
        dlg = wx.FileDialog(
            self,
            message="Open Plexon plx file...",
            defaultDir=self.currentOpenDir,
            wildcard=file_choices,
            style=wx.OPEN|wx.CHANGE_DIR)
        if self.opened_file is not None:
            dlg.SetFilename(self.opened_file)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.opened_file = os.path.basename(path)
            self.currentOpenDir = os.path.dirname(path)
            self.flash_status_message("Opening file %s ..." % path, flash_len_ms=1000)
            self.chart_panel.open_file(path,self.progress_bar_on_update)
            self.SetTitle(self.title + ' - ' + os.path.basename(path))
    
    def on_append_data(self, _event):
        file_choices = "PLX (*.plx)|*.plx"
        dlg = wx.FileDialog(
            self,
            message="Open Plexon plx file...",
            defaultDir=self.currentOpenDir,
            wildcard=file_choices,
            style=wx.OPEN|wx.CHANGE_DIR)
        if self.opened_file is not None:
            dlg.SetFilename(self.opened_file)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.opened_file = os.path.basename(path)
            self.currentOpenDir = os.path.dirname(path)
            self.flash_status_message("Opening file %s ..." % path, flash_len_ms=1000)
            self.chart_panel.append_data(path,self.progress_bar_on_update)
            self.SetTitle(self.title + ' - ' + os.path.basename(path))
    
    def on_clear_data(self, _event):
        self.chart_panel.clear_data()
        self.SetTitle(self.title)
        
    def on_save_data(self, _event):
        file_choices = "PKL (*.pkl)|*.pkl"
        dlg = wx.FileDialog(
            self,
            message="Save data as...",
            defaultDir=self.currentSaveDir,
            wildcard=file_choices,
            style=wx.SAVE|wx.CHANGE_DIR)
        if self.opened_file is not None:
            dlg.SetFilename(os.path.splitext(self.opened_file)[0]+'.pkl')
        if dlg.ShowModal() == wx.ID_OK:
            import pickle
            pkl_file = dlg.GetPath()
            self.currentSaveDir = os.path.dirname(pkl_file)
            data_dict = self.chart_panel.save_data()
            with open(pkl_file, 'wb') as pkl_output:
                pickle.dump(data_dict, pkl_output)
            self.flash_status_message("Saved to %s" % pkl_file)
        
    def on_save_chart(self, _event):
        file_choices = "PNG (*.png)|*.png"
        dlg = wx.FileDialog(
            self,
            message="Save chart as...",
            defaultDir=self.currentSaveDir,
            wildcard=file_choices,
            style=wx.SAVE|wx.CHANGE_DIR)
        if self.opened_file is not None:
            dlg.SetFilename(os.path.splitext(self.opened_file)[0]+'.png')
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.currentSaveDir = os.path.dirname(path)
            self.chart_panel.save_chart(path)
            self.flash_status_message("Saved to %s" % path)
    
    def on_exit(self, _event):
        self.Destroy()
        
    def on_data_updated(self, event):
        pass

    def on_start_data(self, _event):
        self.chart_panel.start_data()
        self.flash_status_message("Data collecting started")
    
    def on_stop_data(self, _event):
        self.chart_panel.stop_data()
        self.statusbar.SetStatusText('', 2)
        self.flash_status_message("Data collecting stopped")
    
    def on_restart_data(self, _event):
        self.chart_panel.restart_data()
        self.statusbar.SetStatusText('', 2)
        self.flash_status_message("Data collecting restarted")
        
    def on_export_chart(self, event):
        path = event.get_path()
        self.chart_panel.save_chart(path)
        self.flash_status_message("Exporting chart to %s" %path)
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg, 0)
        self.status_msg_offtimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.on_flash_status_off,self.status_msg_offtimer)
        self.status_msg_offtimer.Start(flash_len_ms, oneShot=True)

    def on_flash_status_off(self, _event):
        self.statusbar.SetStatusText('', 0)
        
class RCPanel(Pyro.core.ObjBase):
    """
        Interface for remote controlled panel
    """
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
    
    def set_title(self, title):
        #self.set_title_request = title
        parent = wx.FindWindowByName('main_frame')
        parent.SetTitle(parent.title + ' - ' + title)
        
    def clear_title(self):
        #self.clear_title_request = True
        parent = wx.FindWindowByName('main_frame')
        parent.SetTitle(parent.title)
        
    def start_data(self):
        #self.start_request = True
        parent = wx.FindWindowByName('main_frame')
        evt = wx.CommandEvent(EVT_DATA_STOP_TYPE)
        wx.PostEvent(parent, evt)
        
    def stop_data(self):
        #self.stop_request = True
        parent = wx.FindWindowByName('main_frame')
        evt = wx.CommandEvent(EVT_DATA_STOP_TYPE)
        wx.PostEvent(parent, evt)
        
    def restart_data(self):
        #self.restart_request = True
        parent = wx.FindWindowByName('main_frame')
        evt = wx.CommandEvent(EVT_DATA_RESTART_TYPE)
        wx.PostEvent(parent, evt)
        
    def export_chart(self, path):
        parent = wx.FindWindowByName('main_frame')
        evt = ExportChartEvent(EVT_EXPORT_CHART_TYPE, -1, path)
        wx.PostEvent(parent, evt)
        
    def close(self):
        #self.close_request = True
        parent = wx.FindWindowByName('main_frame')
        evt = wx.CommandEvent(EVT_FRAME_CLOSE_TYPE)
        wx.PostEvent(parent, evt)
        
def adjust_spines(ax,spines,spine_outward=['left','right'],xoutward=0,youtward=5,xticks='bottom',yticks='left',\
                  xtick_dir='out',ytick_dir='out',tick_label=['x','y'],xaxis_loc=None,yaxis_loc=None,
                  xminor_auto_loc=None,yminor_auto_loc=None,
                  xmajor_loc=None,ymajor_loc=None):
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
    if xmajor_loc is not None:
        ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(xmajor_loc))
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
    if ymajor_loc is not None:
        ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(ymajor_loc))
    if yticks is 'none':
        ax.yaxis.set_ticks([])
    if 'y' not in tick_label:
        ax.yaxis.set_ticklabels([])
    ax.yaxis.set_ticks_position(yticks)
    ax.yaxis.set_tick_params(which='both',direction=ytick_dir)
    