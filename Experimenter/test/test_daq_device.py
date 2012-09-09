# Test daq device.
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import time
import Pyro.core
import threading
import Queue
from SpikeRecord.Plexon.PlexClient import PlexClient
from SpikeRecord.Plexon.PlexUtil import PlexUtil
from Experimenter.Experiments.Experiment import ExperimentConfig,Experiment

class SoftTriggerReceiver(Pyro.core.ObjBase):
    """ Trigger stamps receiver
    """
    def __init__(self,host,port):
        Pyro.core.ObjBase.__init__(self)
        self.server_host = host
        self.disp_queue = Queue.Queue()
        self.comp_queue = Queue.Queue()
        threading.Thread(target=self.create_pyro_server,kwargs={'host':host,'port':port}).start()
        
    def put_stamp(self, value):
        self.disp_queue.put_nowait(value)
        self.comp_queue.put_nowait(value)
        
    def get_comp_stamp(self):
        return self.comp_queue.get(timeout=3.0)
    
    def get_all_stamps(self):
        stamp_list = []
        try:
            while True:
                stamp_list.append(self.disp_queue.get_nowait())
        except:
            pass
        return stamp_list
        
    def create_pyro_server(self,host,port):
        Pyro.config.PYRO_MULTITHREADED = 0
        Pyro.core.initServer()
        self.pyro_daemon = Pyro.core.Daemon(host=host,port=port)
        self.PYRO_URI = self.pyro_daemon.connect(self, 'trigger_receiver')
        if self.pyro_daemon.port is not port:
            raise RuntimeError("Pyro daemon cannot run on port %d. " %port +
                               "Probably the port has already been taken up by another pyro daemon.")
        self.pyro_daemon.requestLoop()

class TestDAQTriggerExp(Experiment):
    """ Test DAQ device experiment.
    """
    def __init__(self,receiver_host,receiver_port,params,*args,**kwargs):
        super(TestDAQTriggerExp, self).__init__(*args,**kwargs)
        self.source = 'sparsenoise_test_daq.py'
        self.exp_name = ExperimentConfig.CELLPREFIX + '-daq-test'
        self.receiver_host = receiver_host
        self.receiver_port = receiver_port
        self.params = params
        self.assignments = ["trigger_receiver_host = '%s'" %self.receiver_host,
                            "trigger_receiver_port = %d" %self.receiver_port ]
        self.pc = PlexClient()
        self.pc.InitClient()
        self.pu = PlexUtil()
        
    def run(self):
        super(TestDAQTriggerExp, self).run()
        self.run_stimulus(left_params=self.params, assignments=self.assignments)
        self.test(mode="strobed")
        
    def test(self, mode="strobed"):
        """ Stimulus will run on StimServer with a regular stamp controller posting 
            stamps via DAQ device and a soft stamp controller writting stamps to a 
            trigger receiver running at receiver host. The sweep stamps of both controllers 
            are the same. And a PlexClient is started to collect stamps sent by DAQ device.
            In the meantime, a pyro server is started to receive stamps send by soft stamp 
            controller. And the stamps are compared between two receivers to see if the
            stamps are pairly identical.
        """
        trig_receiver = SoftTriggerReceiver(host=self.receiver_host,port=self.receiver_port)
        
        DAQ_nstamps = 0
        Soft_nstamps = 0
        failed_times = 0
        finished = False
        while not finished:
            data = self.pc.GetTimeStampArrays()
            if mode == "strobed":
                daq_stamps = self.pu.GetExtEvents(data, event='first_strobe_word')
            elif mode == "unstrobed":
                daq_stamps = self.pu.GetExtEvents(data, event='unstrobed_word')
            DAQ_nstamps += len(daq_stamps['value'])
            daq_words_str = ','.join(str(stamp) for stamp in daq_stamps['value'])
            
            soft_stamps = trig_receiver.get_all_stamps()
            Soft_nstamps += len(soft_stamps)
            soft_words_str = ','.join(str(stamp) for stamp in soft_stamps)
            with open("test_daq_device.txt",'a') as self.output:
                if len(daq_words_str) > 0:
                    self._log_test("Found daq trigger words: %s" %daq_words_str)
                if len(soft_words_str) > 0:
                    self._log_test("Found soft trigger words: %s" %soft_words_str)
                for index,(value,timestamp) in enumerate(zip(daq_stamps['value'],daq_stamps['timestamp'])) :
                    self._log_test("Stamp index:%d" % index)
                    self._log_test("Found DAQ stamps:%d, Soft stamps:%d" % (DAQ_nstamps, Soft_nstamps))
                    self._log_test("found daq  trigger word: %d t=%f" % (value,timestamp))
                    try:
                        soft_stamp = trig_receiver.get_comp_stamp()
                    except:
                        self._log_test("found no soft trigger word")
                        break
                    self._log_test("found soft trigger word: %d" %soft_stamp)
                    try:
                        assert value == soft_stamp
                    except:
                        failed_times += 1
                        self._log_test("Assertion failed:\n\tDAQ stamp:\t%d\t(%s)\tt=%f\n\tSoft stamp:\t%d\t(%s)" \
                            % (value,bin(value),timestamp,soft_stamp,bin(soft_stamp)))
                    self._log_test("Assertion failed times:%d\n" % failed_times)
            time.sleep(1.0)
    def _log_test(self, line):
        print(line)
        self.output.writelines(line + "\n")
    
if __name__ == '__main__':
    ExperimentConfig(data_base_dir='data_test',stim_server_host='192.168.1.1',new_cell=True)
    p_left, p_right = Experiment().get_params()
    TestDAQTriggerExp(receiver_host='192.168.1.2',receiver_port=8118,params=p_left).run()
    