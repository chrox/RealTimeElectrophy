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
        return self.comp_queue.get(timeout=10.0)
    
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
        
    def run(self):
        super(TestDAQTriggerExp, self).run()
        self.run_stimulus(left_params=self.params, assignments=self.assignments)
        self.test()
        
    def test(self):
        """ Stimulus will run on StimServer with a regular stamp controller posting 
            stamps via DAQ device and a soft stamp controller writting stamps to a 
            trigger receiver running at receiver host. The sweep stamps of both controllers 
            are the same. And a PlexClient is started to collect stamps sent by DAQ device.
            In the meantime, a pyro server is started to receive stamps send by soft stamp 
            controller. And the stamps are compared between two receivers to see if the
            stamps are pairly identical.
        """
        trig_receiver = SoftTriggerReceiver(host=self.receiver_host,port=self.receiver_port)
        with PlexClient() as pc:
            pu = PlexUtil()
            while True:
                data = pc.GetTimeStampArrays()
                unstrobed_word = pu.GetExtEvents(data, event='unstrobed_word')
                words_str = ','.join(str(stamp) for stamp in trig_receiver.get_all_stamps())
                if len(words_str) > 0:
                    print "found soft trigger words: %s" %words_str
                for value,timestamp in zip(unstrobed_word['value'],unstrobed_word['timestamp']) :
                    print "found event:unstrobed word:%d t=%f" % (value,timestamp)
                    soft_stamp = trig_receiver.get_comp_stamp()
                    print "found soft trigger word: %d" %soft_stamp
                    assert value == soft_stamp
                time.sleep(1.0)

if __name__ == '__main__':
    ExperimentConfig(data_base_dir='data_test',stim_server_host='192.168.1.105',new_cell=True)
    p_left, p_right = Experiment().get_params()
    TestDAQTriggerExp(receiver_host='192.168.1.105',receiver_port=8118,params=p_left).run()
    