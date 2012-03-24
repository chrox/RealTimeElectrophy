# -*- coding: UTF-8 -*-
#
# Base class of all experiments.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import os
import re
import wx
import time
import Pyro
import threading
import logging
from StimControl.ControlCmd import StimCommand
from Experimenter.GUI.PSTHAverage import PyroPSTHFrame

class ExperimentConfig(object):
    """ Define essential parameters before running real experiment.
    """ 
    BASEDIR = None
    CELLDIR = None
    CELLINDEX = None
    CELLPREFIX = None
    
    def __init__(self,data_base_dir='.',exp_base_dir='.',
                  stim_server_host='localhost',stim_server_port=7766,new_cell=True):
        ExperimentConfig.STIM_SERVER_HOST = stim_server_host
        ExperimentConfig.STIM_SERVER_PORT = stim_server_port
        ExperimentConfig.DATABASEDIR = data_base_dir
        ExperimentConfig.EXPBASEDIR = exp_base_dir
        if not os.path.exists(data_base_dir):
            os.makedirs(data_base_dir)
        if new_cell:
            self.find_new_cell_index()
            self.make_new_cell_dir()
            
            ############# Logging #############
            logfile = ExperimentConfig.CELLDIR+ os.path.sep + ExperimentConfig.CELLPREFIX + '.log'
            logger = logging.getLogger('Experimenter.Experiments')
            logger.setLevel( logging.INFO )
            log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
            log_handler_logfile = logging.FileHandler(logfile)
            log_handler_logfile.setFormatter(log_formatter)
            logger.addHandler(log_handler_logfile)
    
    def find_new_cell_index(self):
        cell_indices = [self.get_index_from_name(name) for name in os.listdir(ExperimentConfig.DATABASEDIR) \
                        if os.path.isdir(ExperimentConfig.DATABASEDIR + os.path.sep + name)]
        if cell_indices:
            ExperimentConfig.CELLINDEX = max(cell_indices)+1
        else:
            ExperimentConfig.CELLINDEX = 0
            
    def make_new_cell_dir(self):
        ExperimentConfig.CELLPREFIX = 'c' + str(ExperimentConfig.CELLINDEX).zfill(2)
        ExperimentConfig.CELLDIR = ExperimentConfig.DATABASEDIR + os.path.sep + ExperimentConfig.CELLPREFIX
                                  
        assert not os.path.exists(ExperimentConfig.CELLDIR)
        os.makedirs(ExperimentConfig.CELLDIR)
        
    def get_index_from_name(self, name):
        # one cell will have a file like cx (x is the index of this cell).
        re_results = re.compile(r'^c(\d+)$').findall(name)
        index = int(re_results[0]) if re_results else -1
        return index
        
class Experiment(object):
    def __init__(self):
        self.stimulus = StimCommand(server_hostname=ExperimentConfig.STIM_SERVER_HOST)
        self.exp_name = None
        self.post_fix = None
        
        self.logger = logging.getLogger('Experimenter.Experiments')
        
    def get_params(self):
        return self.stimulus.get_params()
    
    def run(self):
        pass
        
    def run_stimulus(self, left_params=None, right_params=None, assignments=[]):
        exp_file = ExperimentConfig.EXPBASEDIR + os.path.sep + self.source 
        self.logger.info('Running script: ' + exp_file)
        self.logger.info('Experiment name is: ' + self.exp_name)
        self.logger.info('Experiment time is: ' + time.strftime('%Y/%m/%d %H:%M:%S', time.localtime()))
        self.stimulus.run(exp_file,left_params,right_params,assignments)
        time.sleep(2.0)
        
    def wait_for_stim(self):
        self.logger.info('Waiting for stimulus...')
        while self.stimulus.is_running():
            time.sleep(1.0)
            
    def psth_analysis(self, psth_type=None):
        try:
            psth_server = self.get_psth_server()
            self.psth_setup(psth_server)
            self.wait_for_stim()
            data = psth_server.get_data()
            results = self.extract_results(data)
            chart_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.png'
            self.logger.info('Exporting chart to: ' + chart_file)
            psth_server.export_chart(chart_file)
            self.logger.info('Restarting psth data.')
            psth_server.restart_psth()
        except:
            self.logger.error('Failed to invoke some psth methods.')
        else:
            return results
        
    def get_psth_server(self):
        self.logger.info('Fetching psth server.')
        app = wx.GetApp()
        if app is None:
            self.logger.info('Creating new psth app.')
            threading.Thread(target=self.launch_psth_app).start()
            time.sleep(3.0)
        else:
            self.logger.info('Psth app has been launched.')
        
        URI = "PYROLOC://localhost:6743/%s" % ('psth_server')
        Pyro.core.initClient()
        return Pyro.core.getProxyForURI(URI)
    
    def launch_psth_app(self):
        app = wx.PySimpleApp()
        frame = PyroPSTHFrame()
        frame.Show()
        app.SetTopWindow(frame)
        app.MainLoop()
        
    def psth_setup(self, psth_server):
        pass
    
class ManbarExp(Experiment):
    def __init__(self,left_params,right_params,*args,**kwargs):
        super(ManbarExp, self).__init__(*args,**kwargs)
        self.source = 'manbar.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-manbar'
        
    def run(self):
        super(ManbarExp, self).run()
        self.run_stimulus()
        self.wait_for_stim()
        return self.get_params()
    
class MangratingExp(Experiment):
    def __init__(self,left_params,right_params,*args,**kwargs):
        super(MangratingExp, self).__init__(*args,**kwargs)
        self.source = 'mangrating.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-mangrating'
        
    def run(self):
        super(MangratingExp, self).run()
        self.run_stimulus()
        self.wait_for_stim()
        return self.get_params()
    
class ORITunExp(Experiment):
    def __init__(self,eye,params,*args,**kwargs):
        super(ORITunExp, self).__init__(*args,**kwargs)
        self.source = 'orientation_tuning.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-ori-tun-' + eye
        self.eye = eye
        self.params = params
        self.assignments = ["eye = '%s'" %eye]
        
    def run(self):
        super(ORITunExp, self).run()
        if self.eye == 'left':
            self.run_stimulus(left_params=self.params, assignments=self.assignments)
        elif self.eye == 'right':
            self.run_stimulus(right_params=self.params, assignments=self.assignments)
        ori = self.psth_analysis()
        return ori
    
    def psth_setup(self, psth_server):
        self.logger.info('Uncheck curve fitting for this experiment.')
        psth_server.uncheck_fitting()
        
    def extract_results(self, data):
        if 'max_param' not in data:
            self.logger.error('Failed to get optimal parameter from %s experiment.' %self.exp_name)
        else:
            self.logger.info('Get optimal parameter from %s experiment: %f' %(self.exp_name, data['max_param']))
            return data['max_param']
    
class SPFTunExp(Experiment):
    def __init__(self,eye,params,*args,**kwargs):
        super(SPFTunExp, self).__init__(*args,**kwargs)
        self.source = 'spatial_freq_tuning.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-spf-tun-' + eye
        self.eye = eye
        self.params = params
        self.assignments = ["eye = '%s'" %eye]
        
    def run(self):
        super(SPFTunExp, self).run()
        if self.eye == 'left':
            self.run_stimulus(left_params=self.params, assignments=self.assignments)
        elif self.eye == 'right':
            self.run_stimulus(right_params=self.params, assignments=self.assignments)
        spf = self.psth_analysis()
        return spf
    
    def psth_setup(self, psth_server):
        self.logger.info('Choose Gaussian curve fitting.')
        psth_server.check_fitting('gauss')
        
    def extract_results(self, data):
        if 'max_param' not in data:
            self.logger.error('Failed to get optimal parameter from %s experiment.' %self.exp_name)
        else:
            self.logger.info('Get optimal parameter from %s experiment: %f' %(self.exp_name, data['max_param']))
            return data['max_param']
    
class PHATunExp(Experiment):
    def __init__(self,eye,params,*args,**kwargs):
        super(PHATunExp, self).__init__(*args,**kwargs)
        self.source = 'phase_tuning.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-pha-tun-' + eye
        self.eye = eye
        self.params = params
        self.assignments = ["eye = '%s'" %eye]
        
    def run(self):
        super(PHATunExp, self).run()
        if self.eye == 'left':
            self.run_stimulus(left_params=self.params, assignments=self.assignments)
        elif self.eye == 'right':
            self.run_stimulus(right_params=self.params, assignments=self.assignments)
        pha = self.psth_analysis()
        return pha
    
    def psth_setup(self, psth_server):
        self.logger.info('Choose Gabor curve fitting.')
        psth_server.uncheck_fitting()
        
    def extract_results(self, data):
        if 'max_param' not in data:
            self.logger.error('Failed to get optimal parameter from %s experiment.' %self.exp_name)
        else:
            self.logger.info('Get optimal parameter from %s experiment: %f' %(self.exp_name, data['max_param']))
            return data['max_param']
    
class DSPTunExp(Experiment):
    def __init__(self,left_params,right_params,repeats,postfix,*args,**kwargs):
        super(DSPTunExp, self).__init__(*args,**kwargs)
        self.source = 'disparity_tuning.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-dsp-tun-' + postfix
        self.eye = ['left','right']
        self.left_params = left_params
        self.right_params = right_params
        self.repeats = repeats
        self.assignments = ['repeats = %f' %repeats]
        
    def run(self):
        super(DSPTunExp, self).run()
        self.run_stimulus(self.left_params,self.right_params,assignments=self.assignments)
        pha = self.psth_analysis()
        return pha
    
    def psth_setup(self, psth_server):
        self.logger.info('Choose Sinusoid curve fitting.')
        psth_server.check_fitting('sin')
        
    def extract_results(self, data):
        if 'max_param' not in data:
            self.logger.error('Failed to get optimal parameter from %s experiment.' %self.name)
        else:
            self.logger.info('Get optimal parameter from %s experiment: %f' %(self.name, data['max_param']))
            return data['max_param']

class StimTimingExp(Experiment):
    def __init__(self,left_phase,right_phase,interval,duration,postfix,*args,**kwargs):
        super(StimTimingExp, self).__init__(*args,**kwargs)
        self.source = 'timesetgrating.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-stim-timing-' + postfix
        self.eye = ['left','right']
        self.assignments = ['p_left.phase0 = %f' %left_phase, 'p_right.phase0 = %f' %right_phase, 
                            'stim_interval = %f' %interval, 'repeats = %d' %(duration*1600//3.55)]
        
    def run(self):
        super(DSPTunExp, self).run()
        self.run_stimulus(assignments=self.assignment)
        self.wait_for_stim()

class RestingExp(Experiment):
    def __init__(self,duration,postfix,*args,**kwargs):
        super(RestingExp, self).__init__(*args,**kwargs)
        self.source = 'resting.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + 'resting' + postfix
        self.eye = ['left','right']
        self.assignments = ['duration = %f' %(duration*60.0)]
        
    def run(self):
        super(DSPTunExp, self).run()
        self.run_stimulus(assignments=self.assignment)
        self.wait_for_stim()

if __name__ == '__main__':
    ExperimentConfig(data_base_dir='data',exp_base_dir='.',stim_server_host='192.168.1.105',new_cell=True)
    p_left, p_right = Experiment().get_params()
    ori = ORITunExp(eye='left', params=None).run()
    print ori
    
