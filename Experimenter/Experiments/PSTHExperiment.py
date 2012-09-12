# PSTH experiments
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import os
import sys
import time
import Pyro.core
import subprocess
from Experiment import ExperimentConfig,Experiment

class PSTHExperiment(Experiment):
    PSTH_SERVER_PROCESS = None
    PSTH_SERVER_PORT = 6743
    def psth_analysis(self, psth_type=None):
        #self.psth_server = self.get_psth_server()
        try:
            self.psth_server = self.get_psth_server()
        except Exception,e:
            self.logger.error('Failed to get psth app. ' + str(e))
        
        #self.psth_server.start_psth()
        try:
            self.logger.info('Starting psth data.')
            self.psth_server.start_data()
        except Exception,e:
            self.logger.error('Failed to start psth app. ' + str(e))
        
        try:
            self.logger.info('Setting up psth app.')
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
            # wait for complete of preceding pyro operationsg
            time.sleep(3.0)
            self.logger.info('Stopping psth data.')
            self.psth_server.stop_data()
        except Exception,e:
            self.logger.error('Failed to stop psth app. ' + str(e))
            
        try:
            self.psth_server.clear_title()
        except Exception,e:
            self.logger.error('Failed to clear psth title. ' + str(e))
            
        try:
            return results
        except Exception,e:
            self.logger.error('Failed to return psth result. ' + str(e))
            
    def log_psth_data(self, data):
        data_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.csv'
        param = self.exp_param
        with open(data_file,'w') as data_output:
            if 'param' in data:
                data_output.writelines('param,%s\n' %data['param'])
            if 'x' in data:
                data_output.writelines('%s,%s\n' %(param , ','.join([str(x) for x in data['x']])))
            if 'means' in data:
                data_output.writelines('means,%s\n' % ','.join([str(mean) for mean in data['means']]))
            if 'stds' in data:
                data_output.writelines('stds,%s\n' % ','.join([str(std) for std in data['stds']]))
            if 'max_param' in data:
                data_output.writelines('opt %s,%s\n' %(param , str(data['max_param'])))
            if 'max_value' in data:
                data_output.writelines('opt rate,%s\n' % str(data['max_value']))
            if 'min_param' in data:
                data_output.writelines('nul %s,%s\n' %(param , str(data['min_param'])))
            if 'max_value' in data:
                data_output.writelines('nul rate,%s\n' % str(data['min_value']))
            if 'F1/F0' in data:
                data_output.writelines('F1/F0,%s\n' % str(data['F1/F0']))
            if 'BII' in data:
                data_output.writelines('BII,%s\n' % str(data['BII']))
            if 'S/N' in data:
                data_output.writelines('S/N,%s\n' % str(data['S/N']))
                
    def _get_psth_server(self):
        # multiprocessing version !NOT WORKING ON WIN32!
        import multiprocessing
        import Experimenter.Experiments.app.pyro_psth as pyro_psth

        PSTH_SERVER_PORT = 6743
        self.logger.info('Fetching psth server.')
        try:
            if not Experiment.psth_server_process.is_alive():
                self.logger.warning('PSTH server is dead.')
                raise
        except:
            self.logger.info('Creating new psth app.')
            #Experiment.psth_server_process = multiprocessing.Process(target=launch_psth_app,kwargs={'port':PSTH_SERVER_PORT})
            Experiment.psth_server_process = multiprocessing.Process(target=pyro_psth.launch_psth_app)
            Experiment.psth_server_process.start()
            time.sleep(5.0)
        else:
            self.logger.info('Psth app has been launched.')
        
        assert Experiment.psth_server_process.is_alive()
        URI = "PYROLOC://localhost:%d/%s" % (PSTH_SERVER_PORT, 'psth_server')
        Pyro.core.initClient()
        return Pyro.core.getProxyForURI(URI)
    
    def get_psth_server(self):
        self.logger.info('Fetching psth server.')
        try:
            if PSTHExperiment.PSTH_SERVER_PROCESS.poll() is not None:
                self.logger.warning('PSTH server is dead.')
                raise
        except:
            self.logger.info('Creating new psth app.')
            psth_app_path = os.path.dirname(__file__) + os.path.sep + 'app' + os.path.sep + 'pyro_psth.py'
            args = [sys.executable, psth_app_path, str(PSTHExperiment.PSTH_SERVER_PORT)]
            PSTHExperiment.PSTH_SERVER_PROCESS = subprocess.Popen(args)
            time.sleep(3.0)                
        else:
            self.logger.info('Psth app has been launched.')
        assert PSTHExperiment.PSTH_SERVER_PROCESS.poll() is None
        URI = "PYROLOC://localhost:%d/%s" % (PSTHExperiment.PSTH_SERVER_PORT, 'psth_server')
        Pyro.core.initClient()
        return Pyro.core.getProxyForURI(URI)
        
    def psth_setup(self):
        self.psth_server.set_title(self.exp_name)
    
class ORITunExp(PSTHExperiment):
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
            return float(data['max_param'])
    
class SPFTunExp(PSTHExperiment):
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
            return float(data['max_param'])
    
class PHATunExp(PSTHExperiment):
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
            return float(data['max_param'])
    
class DSPTunExp(PSTHExperiment):
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
            return float(data['max_param'])
        