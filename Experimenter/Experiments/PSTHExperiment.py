# PSTH experiments
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from __future__ import division
import os
import sys
import time
import Pyro.core
import subprocess
from Experiment import ExperimentConfig,Experiment

class PSTHExperiment(Experiment):
    PSTH_SERVER_PROCESS = None
    PSTH_SERVER_PORT = 6743
    def __init__(self,*args,**kwargs):
        super(PSTHExperiment, self).__init__(*args,**kwargs)
        self.pyro_source = ''
        self.exp_param = ''
        
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
            self.logger.info('Setting up psth app before stimulation.')
            self.pre_stim_setup()
        except Exception,e:
            self.logger.error('Failed to setup psth app. ' + str(e))
        
        try:
            self.wait_for_stim()
        except Exception,e:
            self.logger.error('Failed to wait for stimulation. ' + str(e))
            
        try:
            self.logger.info('Setting up psth app after stimulation.')
            self.post_stim_setup()
        except Exception,e:
            self.logger.error('Failed to setup psth app. ' + str(e))
        
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
            # wait for complete of preceding pyro operationsg
            time.sleep(3.0)
            self.logger.info('Closing psth server.')
            self.psth_server.close()
        except Exception,e:
            self.logger.error('Failed to close psth server. ' + str(e))
            
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
    
    def get_psth_server(self):
        self.logger.info('Fetching psth server.')
        try:
            if PSTHExperiment.PSTH_SERVER_PROCESS.poll() is not None:
                self.logger.info('PSTH server is dead.')
                raise
        except:
            self.logger.info('Creating new psth app.')
            psth_app_path = os.path.dirname(__file__) + os.path.sep + 'app' + os.path.sep + self.pyro_source
            args = [sys.executable, psth_app_path, str(PSTHExperiment.PSTH_SERVER_PORT)]
            PSTHExperiment.PSTH_SERVER_PROCESS = subprocess.Popen(args)
            time.sleep(3.0)                
        else:
            self.logger.info('Psth app has been launched.')
        assert PSTHExperiment.PSTH_SERVER_PROCESS.poll() is None
        URI = "PYROLOC://localhost:%d/%s" % (PSTHExperiment.PSTH_SERVER_PORT, 'psth_server')
        Pyro.core.initClient()
        return Pyro.core.getProxyForURI(URI)
        
    def pre_stim_setup(self):
        self.psth_server.set_title(self.exp_name)
        
    def post_stim_setup(self):
        pass
        
    def extract_results(self, _data):
        raise RuntimeError("Must override extract_results method with exp implementation!")
    
class ORITunExp(PSTHExperiment):
    def __init__(self,eye,params,*args,**kwargs):
        super(ORITunExp, self).__init__(*args,**kwargs)
        self.pyro_source = 'pyro_psth_tuning.py'
        self.stim_source = 'orientation_tuning.py'
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
    
    def pre_stim_setup(self):
        super(ORITunExp, self).pre_stim_setup()
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
        self.pyro_source = 'pyro_psth_tuning.py'
        self.stim_source = 'spatial_freq_tuning.py'
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
    
    def pre_stim_setup(self):
        super(SPFTunExp, self).pre_stim_setup()
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
        self.pyro_source = 'pyro_psth_tuning.py'
        self.stim_source = 'phase_tuning.py'
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
    
    def pre_stim_setup(self):
        super(PHATunExp, self).pre_stim_setup()
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
        self.pyro_source = 'pyro_psth_tuning.py'
        self.stim_source = 'disparity_tuning.py'
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
    
    def pre_stim_setup(self):
        super(DSPTunExp, self).pre_stim_setup()
        self.logger.info('Choose Sinusoid curve fitting.')
        self.psth_server.check_fitting('sin')
        
    def extract_results(self, data):
        if 'max_param' not in data:
            self.logger.error('Failed to get optimal parameter from %s experiment.' %self.exp_name)
        else:
            self.logger.info('Get optimal parameter from %s experiment: %f' %(self.exp_name, data['max_param']))
            return float(data['max_param'])

class SpikeLatencyExp(PSTHExperiment):
    def __init__(self,eye,params,*args,**kwargs):
        super(SpikeLatencyExp, self).__init__(*args,**kwargs)
        self.pyro_source = 'pyro_psth_average.py'
        self.stim_source = 'rand_phase.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-latency-' + eye
        self.exp_param = 'lat'
        self.eye = eye
        self.params = params
        self.assignments = ["eye = '%s'" %eye]
        
    def run(self):
        super(SpikeLatencyExp, self).run()
        if self.eye == 'left':
            self.run_stimulus(left_params=self.params, assignments=self.assignments)
        elif self.eye == 'right':
            self.run_stimulus(right_params=self.params, assignments=self.assignments)
        latency = self.psth_analysis()
        return latency
    
    def pre_stim_setup(self):
        super(SpikeLatencyExp, self).pre_stim_setup()
        
    def extract_results(self, data):
        if 'maxima' not in data:
            self.logger.error('Failed to get spike latency from %s experiment.' %self.exp_name)
        else:
            index = data['maxima'].argmax()
            maximum = data['maxima_index'][index]
            self.logger.info('Get spike latency from %s experiment: %f' %(self.exp_name, maximum))
            return maximum/1000.0
        
    def log_psth_data(self, data):
        data_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.csv'
        data = ''
        if 'time' in data and 'psth' in data:
            data += 'Time,Value\n'
            for index in data['time']:
                data += '{0},{1:.2f}\n'.format(data['time'][index],data['psth'][index])
        extrima = ''
        if 'maxima_indices' in data and 'maxima' in data:
            extrima += 'Maxima,Value\n'
            for index in data['maxima_indices']:
                extrima += '{0},{1:.2f}\n'.format(data['maxima_indices'][index],data['maxima'][index])
        if 'minima_indices' in data and 'minima' in data:
            extrima += 'Minima,Value\n'
            for index in data['minima_indices']:
                extrima += '{0},{1:.2f}\n'.format(data['minima_indices'][index],data['minima'][index])
        with open(data_file,'w') as data_output:
            data_output.writelines(data + extrima)
            