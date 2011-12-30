# GUI control of visual stimulation extended from VisionEgg.PyroApps.EPhysGUI

import os
import datetime
import Tkinter
import VisionEgg.PyroApps
import VisionEgg.PyroApps.EPhysGUI as gui

client_list = []
client_list.extend(VisionEgg.PyroApps.DropinGUI.get_control_list())

class AppWindow(gui.AppWindow):
    def __init__(self,
                 master=None,
                 client_list=None,
                 server_hostname='',
                 server_port=7766,
                 **cnf):

        if hasattr(VisionEgg, '_exception_hook_keeper'):
            # Keep original exception handler
            self._orig_report_callback_exception = Tkinter.Tk.report_callback_exception
            self._tk = Tkinter.Tk
            # Use Vision Egg exception handler
            Tkinter.Tk.report_callback_exception = VisionEgg._exception_hook_keeper.handle_exception

        # Allow VisionEgg Tkinter exception window
        VisionEgg.config._Tkinter_used = True

        # create myself
        Tkinter.Frame.__init__(self,master, **cnf)
        self.winfo_toplevel().title("StimControl GUI - RealTimeElectrophy")

        self.client_list = client_list

        self.server_hostname = server_hostname
        self.server_port = server_port

        self.pyro_client = VisionEgg.PyroClient.PyroClient(self.server_hostname,self.server_port)
        self.ephys_server = self.pyro_client.get("ephys_server")
        self.ephys_server.first_connection()

        self.stim_onset_cal_tk_var = Tkinter.BooleanVar()
        self.stim_onset_cal_tk_var.set(0)
        
        params_dir = os.path.abspath(os.curdir) + \
                     os.path.sep + 'params' + \
                     os.path.sep + datetime.datetime.now().strftime('%Y%m%d')
        if not os.path.exists(params_dir):
            os.makedirs(params_dir)
        self.autosave_dir = Tkinter.StringVar()
        self.autosave_dir.set(params_dir)
        self.autosave_basename = Tkinter.StringVar()

        # create menu bar
        self.bar = Tkinter.Menu(tearoff=0)
        top = self.winfo_toplevel()
        top.configure(menu=self.bar)

        self.bar.file_menu = Tkinter.Menu(self.bar, name="file_menu")
        self.bar.add_cascade(label="File",menu=self.bar.file_menu)

        self.bar.file_menu.add_command(label='Save image sequence...', command=self.save_image_sequence)
        self.bar.file_menu.add_command(label='Save configuration file...', command=self.save_config)
        self.bar.file_menu.add_command(label='Load configuration file...', command=self.load_config)
        self.bar.file_menu.add_command(label='Load auto-saved .py parameter file...', command=self.load_params)
        self.bar.file_menu.add_separator()
        self.bar.file_menu.add_command(label='Load LightStim script...', command=self.load_demoscript)
        self.bar.file_menu.add_separator()

        self.quit_server_too = Tkinter.BooleanVar()
        self.quit_server_too.set(1)
        self.bar.file_menu.add_checkbutton(label='Quit server too',
                                           variable=self.quit_server_too)
        self.bar.file_menu.add_command(label='Quit',
                                       command=self.quit,
                                       )

        stimkey = self.ephys_server.get_stimkey()
        self.stimulus_tk_var = Tkinter.StringVar()
        self.stimulus_tk_var.set( stimkey )

        self.bar.stimuli_menu = Tkinter.Menu(self.bar, name="stimuli_menu")
        self.bar.add_cascade(label="Stimuli",menu=self.bar.stimuli_menu)
        for maybe_stimkey, _maybe_control_frame, maybe_title in self.client_list:
            if maybe_title != "Vision Egg Script":
                self.bar.stimuli_menu.add_radiobutton(label=maybe_title,
                                                      command=self.change_stimulus,
                                                      variable=self.stimulus_tk_var,
                                                      value=maybe_stimkey)

        self.bar.calibration_menu = Tkinter.Menu(self.bar, name="calibration_menu")
        self.bar.add_cascade(label="Configure/Calibrate",
                             menu=self.bar.calibration_menu)

        self.bar.calibration_menu.add_command(label='3D Perspective...', command=self.launch_screen_pos)
        self.bar.calibration_menu.add_command(label='Stimulus onset timing...', command=self.launch_stim_onset_cal)
        self.bar.calibration_menu.add_command(label='Load gamma table...', command=self.launch_gamma_panel)
        self.notify_on_dropped_frames = Tkinter.BooleanVar()
        self.notify_on_dropped_frames.set(1)
        self.bar.calibration_menu.add_checkbutton(label='Warn on frame skip',
                                                  variable=self.notify_on_dropped_frames)

        self.override_t_abs_sec = Tkinter.StringVar() # Tkinter DoubleVar loses precision
        self.override_t_abs_sec.set("0.0")

        self.override_t_abs_on = Tkinter.BooleanVar()
        self.override_t_abs_on.set(0)
        self.bar.calibration_menu.add_checkbutton(label='Override server absolute time (CAUTION)',
                                                  variable=self.override_t_abs_on)

        row = 0

        # options for self.stim_frame in grid layout manager
        self.stim_frame_cnf = {'row':row,
                               'column':0,
                               'columnspan':2,
                               'sticky':'nwes'}

        row += 1
        Tkinter.Label(self,
                      text="Sequence information",
                      font=("Helvetica",12,"bold")).grid(row=row,column=0)
        row += 1
        # options for self.loop_frame in grid layout manager
        self.loop_frame_cnf = {'row':row,
                               'column':0,
                               'sticky':'nwes'}

        row -= 1
        Tkinter.Label(self,
                      text="Parameter Save Options",
                      font=("Helvetica",12,"bold")).grid(row=row,column=1)
        row += 1
        self.auto_save_frame = Tkinter.Frame(self)
        asf = self.auto_save_frame # shorthand
        asf.grid(row=row,column=1,sticky="nwes")
        asf.columnconfigure(1,weight=1)

        asf.grid_row = 0
        self.autosave = Tkinter.BooleanVar()
        self.autosave.set(1)
        self.auto_save_button = Tkinter.Checkbutton(asf,
                                                    text="Auto save trial parameters",
                                                    variable=self.autosave)
        self.auto_save_button.grid(row=asf.grid_row,column=0,columnspan=2)

        self.param_file_type_tk_var = Tkinter.StringVar()
        self.param_file_type_tk_var.set("Python format")
        filetype_bar = Tkinter.Menubutton(asf,
                                 textvariable=self.param_file_type_tk_var,
                                 relief=Tkinter.RAISED)
        filetype_bar.grid(row=asf.grid_row,column=2)
        filetype_bar.menu = Tkinter.Menu(filetype_bar,tearoff=0)
        filetype_bar.menu.add_radiobutton(label="Python format",
                                 value="Python format",
                                 variable=self.param_file_type_tk_var)
        filetype_bar.menu.add_radiobutton(label="Matlab format",
                                 value="Matlab format",
                                 variable=self.param_file_type_tk_var)
        filetype_bar['menu'] = filetype_bar.menu

        asf.grid_row += 1
        Tkinter.Label(asf,
                      text="Parameter file directory:").grid(row=asf.grid_row,column=0,sticky="e")
        Tkinter.Entry(asf,
                      textvariable=self.autosave_dir).grid(row=asf.grid_row,column=1,sticky="we")
        Tkinter.Button(asf,
                       text="Set...",command=self.set_autosave_dir).grid(row=asf.grid_row,column=2)
        asf.grid_row += 1
        Tkinter.Label(asf,
                      text="Parameter file basename:").grid(row=asf.grid_row,column=0,sticky="e")
        Tkinter.Entry(asf,
                      textvariable=self.autosave_basename).grid(row=asf.grid_row,column=1,sticky="we")
        Tkinter.Button(asf,
                       text="Reset",command=self.reset_autosave_basename).grid(row=asf.grid_row,column=2)

        row += 1
        Tkinter.Button(self, text='Do single trial', command=self.do_single_trial).grid(row=row,column=0)
        Tkinter.Button(self, text='Do sequence', command=self.do_loops).grid(row=row,column=1)

        row += 1
        self.progress = VisionEgg.GUI.ProgressBar(self,
                                                  width=300,
                                                  relief="sunken",
                                                  doLabel=0,
                                                  labelFormat="%s")
        self.progress.labelText = "Starting..."
        self.progress.updateProgress(0)
        self.progress.grid(row=row,column=0,columnspan=2)#,sticky='we')

        # Allow rows and columns to expand
        for i in range(2):
            self.columnconfigure(i,weight=1)
        for i in range(row+1):
            self.rowconfigure(i,weight=1)

        self.demoscript_filename = ''
        self.vars_list = None
        self.switch_to_stimkey( stimkey )
        
        self.config_dir = None
        

if __name__ == '__main__':
    hostname = 'localhost'
    port = 7766
    result = gui.get_server(hostname=hostname,port=port)
    if result:
        hostname,port = result
        app_window = AppWindow(client_list=client_list,
                               server_hostname=hostname,
                               server_port=port)

        app_window.winfo_toplevel().wm_iconbitmap()
        app_window.pack(expand=1,fill=Tkinter.BOTH)
        app_window.mainloop()
        
