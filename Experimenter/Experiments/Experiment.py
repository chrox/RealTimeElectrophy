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
import pkg_resources
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
        else:
            self.find_current_cell_index()
            self.make_current_cell_dir()
            
        ############# Logging #############
        logfile = ExperimentConfig.CELLDIR+ os.path.sep + ExperimentConfig.CELLPREFIX + '.log'
        logger = logging.getLogger('Experimenter.Experiments')
        logger.setLevel( logging.INFO )
        log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
        log_handler_logfile = logging.FileHandler(logfile)
        log_handler_logfile.setFormatter(log_formatter)
        logger.addHandler(log_handler_logfile)
        
        # log version of RealTimeElectrophy
        try:
            version = pkg_resources.get_distribution("RealTimeElectrophy").version
            logger.info("Experiments performed with RealTimeElectrophy version: " + version)
        except:
            logger.warning("Experiments performed with unkown RealTimeElectrophy version.")
    
    def find_new_cell_index(self):
        cell_indices = [self.get_index_from_name(name) for name in os.listdir(ExperimentConfig.DATABASEDIR) \
                        if os.path.isdir(ExperimentConfig.DATABASEDIR + os.path.sep + name)]
        if cell_indices:
            ExperimentConfig.CELLINDEX = max(cell_indices)+1
        else:
            ExperimentConfig.CELLINDEX = 0
            
    def find_current_cell_index(self):
        cell_indices = [self.get_index_from_name(name) for name in os.listdir(ExperimentConfig.DATABASEDIR) \
                        if os.path.isdir(ExperimentConfig.DATABASEDIR + os.path.sep + name)]
        if cell_indices:
            ExperimentConfig.CELLINDEX = max(cell_indices)
        else:
            ExperimentConfig.CELLINDEX = 0
            
    def make_new_cell_dir(self):
        ExperimentConfig.CELLPREFIX = 'c' + str(ExperimentConfig.CELLINDEX).zfill(2)
        ExperimentConfig.CELLDIR = ExperimentConfig.DATABASEDIR + os.path.sep + ExperimentConfig.CELLPREFIX
                                  
        assert not os.path.exists(ExperimentConfig.CELLDIR)
        os.makedirs(ExperimentConfig.CELLDIR)
        
    def make_current_cell_dir(self):
        ExperimentConfig.CELLPREFIX = 'c' + str(ExperimentConfig.CELLINDEX).zfill(2)
        ExperimentConfig.CELLDIR = ExperimentConfig.DATABASEDIR + os.path.sep + ExperimentConfig.CELLPREFIX
                                  
        if not os.path.exists(ExperimentConfig.CELLDIR):
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
        # sleep for 5 seconds
        time.sleep(5.0)
        self.logger.info('='*18)
        
    def run_stimulus(self, left_params=None, right_params=None, assignments=[]):
        exp_file = ExperimentConfig.EXPBASEDIR + os.path.sep + self.source 
        self.logger.info('Running script: ' + exp_file)
        self.logger.info('Experiment name is: ' + self.exp_name)
        self.logger.info('Experiment time is: ' + time.strftime('%Y/%m/%d %H:%M:%S', time.localtime()))
        self.stimulus.run(exp_file,left_params,right_params,assignments)
        time.sleep(1.0)
        
    def wait_for_stim(self):
        self.logger.info('Waiting for stimulus...')
        while self.stimulus.is_running():
            time.sleep(1.0)
            
    def psth_analysis(self, psth_type=None):
        try:
            self.psth_server = self.get_psth_server()
            self.psth_server.start_psth()
            self.psth_setup()
        except Exception,e:
            self.logger.error('Failed to setup psth app. ' + str(e))
            
        try:
            self.wait_for_stim()
        except Exception,e:
            self.logger.error('Failed to wait for stimulation. ' + str(e))
            
        try:
            data = self.psth_server.get_data()
        except Exception,e:
            self.logger.error('Failed to get data from psth. ' + str(e))
        
        try:
            self.log_psth_data(data)
        except Exception,e:
            self.logger.error('Failed to log psth data. ' + str(e))
        
        try:
            results = self.extract_results(data)
        except Exception,e:
            self.logger.error('Failed to extract psth data. ' + str(e))
        
        try:
            chart_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.png'
            self.logger.info('Exporting chart to: ' + chart_file)
            self.psth_server.export_chart(chart_file)
        except Exception,e:
            self.logger.error('Failed to export psth chart. ' + str(e))
        
        try:
            self.logger.info('Restarting psth data.')
            self.psth_server.restart_psth()
        except Exception,e:
            self.logger.error('Failed to restart psth data. ' + str(e))
            
        try:
            return results
        except Exception,e:
            self.logger.error('Failed to return psth result. ' + str(e))
        
    def log_psth_data(self, data):
        data_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.csv'
        param = self.exp_param
        with open(data_file,'w') as data_output:
            if 'param' in data:
                data_output.write('param,'+data['param'])
            if 'x' in data:
                data_output.write('%s,' %param + ','.join(data['x']))
            if 'means' in data:
                data_output.write('means,'+','.join(data['means']))
            if 'stds' in data:
                data_output.write('stds,'+','.join(data['stds']))
            if 'max_param' in data:
                data_output.write('opt %s,' %param + data['max_param'])
            if 'max_value' in data:
                data_output.write('opt rate,' + data['max_value'])
            if 'min_param' in data:
                data_output.write('nul %s,' %param + data['min_param'])
            if 'max_value' in data:
                data_output.write('nul rate,' + data['min_value'])
            if 'F1/F0' in data:
                data_output.write('F1/F0,' + data['F1/F0'])
            if 'BII' in data:
                data_output.write('BII,' + data['BII'])
            if 'S/N' in data:
                data_output.write('S/N,' + data['S/N'])
        
    def do_no_analysis(self):
        try:
            self.psth_server = self.get_psth_server()
            self.psth_server.stop_psth()
            self.psth_setup()
            self.wait_for_stim()
            self.logger.info('Restarting psth data.')
            self.psth_server.restart_psth()
        except Exception,e:
            self.logger.error('Failed to invoke some psth methods. ' + str(e))
        
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
        
    def psth_setup(self):
        self.psth_server.set_psth_title(self.exp_name)
    
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
        self.exp_param = 'ori'
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
    
    def psth_setup(self):
        super(ORITunExp, self).psth_setup()
        self.logger.info('Uncheck curve fitting for this experiment.')
        self.psth_server.uncheck_fitting()
        
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
        self.exp_param = 'spf'
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
    
    def psth_setup(self):
        super(SPFTunExp, self).psth_setup()
        self.logger.info('Choose Gaussian curve fitting.')
        self.psth_server.check_fitting('gauss')
        
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
        self.exp_param = 'pha'
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
    
    def psth_setup(self):
        super(PHATunExp, self).psth_setup()
        self.logger.info('Uncheck curve fitting.')
        self.psth_server.uncheck_fitting()
        
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
        self.exp_param = 'dsp'
        self.eye = ['left','right']
        self.left_params = left_params
        self.right_params = right_params
        self.repeats = repeats
        self.assignments = ['repeats = %d' %repeats]
        
    def run(self):
        super(DSPTunExp, self).run()
        self.run_stimulus(self.left_params,self.right_params,assignments=self.assignments)
        pha = self.psth_analysis()
        return pha
    
    def psth_setup(self):
        super(DSPTunExp, self).psth_setup()
        self.logger.info('Choose Sinusoid curve fitting.')
        self.psth_server.check_fitting('sin')
        
    def extract_results(self, data):
        if 'max_param' not in data:
            self.logger.error('Failed to get optimal parameter from %s experiment.' %self.exp_name)
        else:
            self.logger.info('Get optimal parameter from %s experiment: %f' %(self.exp_name, data['max_param']))
            return data['max_param']

class StimTimingExp(Experiment):
    def __init__(self,left_phase,right_phase,interval,duration,postfix,rand_phase=False,*args,**kwargs):
        super(StimTimingExp, self).__init__(*args,**kwargs)
        self.source = 'timesetgrating.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-stim-timing-' + postfix
        self.eye = ['left','right']
        self.assignments = ['p_left.phase0 = %f' %left_phase, 'p_right.phase0 = %f' %right_phase, 
                            'stim_interval = %f' %interval, 'repeats = %d' %(duration*1600//3.55),
                            'rand_phase = %r' %rand_phase]
        
    def run(self):
        super(StimTimingExp, self).run()
        self.run_stimulus(assignments=self.assignments)
        self.do_no_analysis()

class RestingExp(Experiment):
    def __init__(self,duration,postfix,*args,**kwargs):
        super(RestingExp, self).__init__(*args,**kwargs)
        self.source = 'resting.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-resting-' + postfix
        self.eye = ['left','right']
        self.assignments = ['duration = %f' %(duration*60.0)]
        
    def run(self):
        super(RestingExp, self).run()
        self.run_stimulus(assignments=self.assignments)
        self.do_no_analysis()

if __name__ == '__main__':
    ExperimentConfig(data_base_dir='data',exp_base_dir='.',stim_server_host='192.168.1.105',new_cell=True)
    p_left, p_right = Experiment().get_params()
    p_left.phase0 = 25.5
    p_right.phase0 = 135.5
    exp_postfix = 'm24-opt'
    RestingExp(duration=5.0, postfix=exp_postfix).run()
    