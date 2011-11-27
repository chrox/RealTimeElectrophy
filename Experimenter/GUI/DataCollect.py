# Core gui elements for data analysis.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import time
import threading
import wx
import matplotlib

EVT_UPDATED_TYPE = wx.NewEventType()
EVT_UPDATED = wx.PyEventBinder(EVT_UPDATED_TYPE, 1)

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
        evt = DataUpdatedEvent(EVT_UPDATED_TYPE, -1, updated_data)
        wx.PostEvent(self._parent, evt)
        
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
        #wx.FindWindowByName('psth_panel').update_chart()
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

        self.Bind(EVT_UPDATED, self.on_data_updated)

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt_data = menu_file.Append(-1, "&Save &data\tCtrl-D", "Save data to file")
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

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.unit_choice, flag=wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border=5)
        #self.hbox.AddSpacer(5)
        self.hbox.Add(self.chart_panel, flag=wx.ALL | wx.ALIGN_RIGHT| wx.ALIGN_CENTER_VERTICAL, border=5)
        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)
        self.panel.Layout()
        
    def create_chart_panel(self):
        pass

    def on_save_data(self, event):
        self.chart_panel.on_save_data(event)
        
    def on_save_chart(self, event):
        self.chart_panel.on_save_chart(event)
    
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