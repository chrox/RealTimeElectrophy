# STA experiments
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import os
import sys
import time
import Pyro
import subprocess
from Experiment import ExperimentConfig,Experiment

class STAExperiment(Experiment):
    STA_SERVER_PROCESS = None
    STA_SERVER_PORT = 6878
    def __init__(self,*args,**kwargs):
        super(STAExperiment, self).__init__(*args,**kwargs)
        self.pyro_source = ''
        self.exp_param = ''
    def sta_analysis(self, sta_type=None):
        # Beware that the pyro operation is asynchronized. It takes several 
        # hundred millseconds for the app to complete action. So it's safe to wait for
        # remote app taking effect before another pyro operation.
        try:
            self.sta_server = self.get_sta_server()
        except Exception,e:
            self.logger.error('Failed to get sta app. ' + str(e))
        
        try:
            self.logger.info('Starting sta data.')
            self.sta_server.start_data()
        except Exception,e:
            self.logger.error('Failed to start sta app. ' + str(e))
        
        try:
            self.logger.info('Setting up sta app before stimulation.')
            self.pre_stim_setup()
        except Exception,e:
            self.logger.error('Failed to setup sta app. ' + str(e))
        
        try:
            self.wait_for_stim()
        except Exception,e:
            self.logger.error('Failed to wait for stimulation. ' + str(e))
        
        try:
            self.logger.info('Setting up sta app after stimulation.')
            self.post_stim_setup()
        except Exception,e:
            self.logger.error('Failed to setup sta app. ' + str(e))
        
        try:
            data = self.sta_server.get_data()
        except Exception,e:
            self.logger.error('Failed to get data from sta. ' + str(e))
        
        try:
            self.log_sta_data(data)
        except Exception,e:
            self.logger.error('Failed to log sta data. ' + str(e))
        
        try:
            results = self.extract_results(data)
        except Exception,e:
            self.logger.error('Failed to extract sta data. ' + str(e))
            
        try:
            # wait for complete of preceding pyro operationsg
            time.sleep(3.0)
            self.logger.info('Stopping sta data.')
            self.sta_server.stop_data()
        except Exception,e:
            self.logger.error('Failed to stop sta app. ' + str(e))
        
        try:
            # wait for complete of preceding pyro operationsg
            time.sleep(3.0)
            self.logger.info('Closing sta server.')
            self.sta_server.close()
        except Exception,e:
            self.logger.error('Failed to close sta server. ' + str(e))
        
        try:
            return results
        except Exception,e:
            self.logger.error('Failed to return sta result. ' + str(e))
    
    def log_sta_data(self, data):
        pass
    
    def get_sta_server(self):
        self.logger.info('Fetching sta server.')
        try:
            if STAExperiment.STA_SERVER_PROCESS.poll() is not None:
                self.logger.info('STA server is dead.')
                raise
        except:
            self.logger.info('Creating new sta app.')
            sta_app_path = os.path.dirname(__file__) + os.path.sep + 'app' + os.path.sep + self.pyro_source
            args = [sys.executable, sta_app_path, str(STAExperiment.STA_SERVER_PORT)]
            STAExperiment.STA_SERVER_PROCESS = subprocess.Popen(args)
            time.sleep(3.0)
        else:
            self.logger.info('Psth app has been launched.')
        assert STAExperiment.STA_SERVER_PROCESS.poll() is None
        URI = "PYROLOC://localhost:%d/%s" % (STAExperiment.STA_SERVER_PORT, 'sta_server')
        Pyro.core.initClient()
        return Pyro.core.getProxyForURI(URI)
    
    def pre_stim_setup(self):
        self.sta_server.set_title(self.exp_name)
        
    def post_stim_setup(self):
        pass
    
    def extract_results(self, _data):
        raise RuntimeError("Must override extract_results method with exp implementation!")
        
class RFCMappingExp(STAExperiment):
    def __init__(self,eye,params,postfix,*args,**kwargs):
        super(RFCMappingExp, self).__init__(*args,**kwargs)
        self.pyro_source = 'pyro_sta.py'
        self.stim_source = 'sparsenoise.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-sparsenoise-' + postfix + '-' + eye
        self.exp_param = 'sn'
        self.eye = eye
        self.params = params
        self.assignments = ["eye = '%s'" %eye]
        
    def run(self):
        super(RFCMappingExp, self).run()
        if self.eye == 'left':
            self.run_stimulus(left_params=self.params, assignments=self.assignments)
        elif self.eye == 'right':
            self.run_stimulus(right_params=self.params, assignments=self.assignments)
        position = self.sta_analysis()
        return position
    
    def pre_stim_setup(self):
        super(RFCMappingExp, self).pre_stim_setup()
        self.logger.info('Choose no image fitting for this experiment.')
        self.sta_server.check_fitting('none')
        
    def post_stim_setup(self):
        super(RFCMappingExp, self).post_stim_setup()
        try:
            chart_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '-raw.png'
            self.logger.info('Exporting raw chart to: ' + chart_file)
            self.sta_server.export_chart(chart_file)
            # wait for asynchronized pyro operation to complete
            time.sleep(0.5)
        except Exception,e:
            self.logger.error('Failed to export sta chart. ' + str(e))
        
        self.logger.info('Choose Gabor fitting.')
        self.sta_server.check_fitting('gabor')
        # wait for asynchronized pyro operation to complete
        time.sleep(2.0)
        
        try:
            chart_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '-fitted.png'
            self.logger.info('Exporting fitted chart to: ' + chart_file)
            self.sta_server.export_chart(chart_file)
            # wait for asynchronized pyro operation to complete
            time.sleep(0.5)
        except Exception,e:
            self.logger.error('Failed to export sta chart. ' + str(e))
        
    def extract_results(self, data):
        if 'peak_time' not in data:
            self.logger.error('Failed to get peak time data from %s experiment.' %self.exp_name)
        else:
            self.logger.info('Get peak response at %.1fms after stimulus onset.' %data['peak_time'])
        if 'rf_center' not in data:
            self.logger.error('Failed to get RF center from %s experiment.' %self.exp_name)
        else:
            orig_pos = self.params['xorigDeg'], self.params['yorigDeg']
            cell_width = self.params['widthDeg']*2.0/32.0
            
            rf_x_pos = orig_pos[0] + cell_width * (data['rf_center'][0]-16)
            rf_y_pos = orig_pos[0] + cell_width * (16-data['rf_center'][1])
            rf_pos = (float(rf_x_pos), float(rf_y_pos))
            self.logger.info('Original RF center: %.2f,%.2f' %orig_pos)
            self.logger.info('Get RF center from %s experiment: %.2f,%.2f' %(self.exp_name,rf_pos[0],rf_pos[1]))
            return rf_pos
        
    def log_sta_data(self, data):
        data_file = ExperimentConfig.CELLDIR + os.path.sep + self.exp_name + '.csv'
        with open(data_file,'w') as data_output:
            if 'peak_time' in data:
                data_output.writelines('peak time,%.1f' %data['peak_time'])
            if 'rf_center' in data:
                data_output.writelines('rf position index,%.2f,%.2f' %(data['rf_center'][0],data['rf_center'][1]))