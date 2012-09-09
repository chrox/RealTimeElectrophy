# -*- coding: UTF-8 -*-
#
# Base class of all experiments.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import os
import re
import time
import logging
from StimControl.ControlCmd import StimCommand

class ExperimentConfig(object):
    """ Define essential parameters before running real experiment.
    """ 
    BASEDIR = None
    CELLDIR = None
    CELLINDEX = None
    CELLPREFIX = None
    
    def __init__(self,data_base_dir='.',stim_server_host='localhost',stim_server_port=7766,new_cell=True):
        ExperimentConfig.STIM_SERVER_HOST = stim_server_host
        ExperimentConfig.STIM_SERVER_PORT = stim_server_port
        ExperimentConfig.DATABASEDIR = data_base_dir
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
        log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
        log_handler_logfile = logging.FileHandler(logfile)
        log_handler_logfile.setFormatter(log_formatter)
        # logging Experimenter
        logger = logging.getLogger('Experimenter')
        logger.setLevel( logging.INFO )
        logger.addHandler(log_handler_logfile)

        # logging StimControl
        stimcontrol_logger = logging.getLogger('StimControl')
        stimcontrol_logger.setLevel( logging.INFO )
        logger.addHandler(log_handler_logfile)
        
        # log version of RealTimeElectrophy
        try:
            import pkg_resources
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
        self.source = None
        self.logger = logging.getLogger('Experimenter.Experiments')
        
    def get_params(self):
        return self.stimulus.get_params()
    
    def run(self):
        # sleep for 5 seconds
        time.sleep(5.0)
        self.logger.info('='*18)
        
    def run_stimulus(self, left_params=None, right_params=None, assignments=[]):
        exp_file = os.path.dirname(__file__) + os.path.sep + 'script' + os.path.sep + self.source
        self.logger.info('Running script: ' + exp_file)
        self.logger.info('Experiment name is: ' + self.exp_name)
        self.logger.info('Experiment time is: ' + time.strftime('%Y/%m/%d %H:%M:%S', time.localtime()))
        try:
            with open(exp_file) as source_file:
                source = source_file.read()
        except IOError:
            self.logger.error('Cannot read stimulation source code.')
            return
        self.stimulus.run(self.exp_name,source,left_params,right_params,assignments)
        time.sleep(1.0)
        
    def wait_for_stim(self):
        self.logger.info('Waiting for stimulus...')
        while self.stimulus.is_running():
            time.sleep(1.0)
        self.logger.info('Writing stimulus log...')
        
        log_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.log'
        with open(log_file, 'w') as log:
            loglines = self.stimulus.get_stimulus_log(self.exp_name)
            log.writelines(loglines)
            
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
        self.wait_for_stim()

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
        self.wait_for_stim()

if __name__ == '__main__':
    ExperimentConfig(data_base_dir='data',exp_base_dir='.',stim_server_host='192.168.1.105',new_cell=True)
    p_left, p_right = Experiment().get_params()
    p_left.phase0 = 25.5
    p_right.phase0 = 135.5
    exp_postfix = 'm24-opt'
    RestingExp(duration=5.0, postfix=exp_postfix).run()
    