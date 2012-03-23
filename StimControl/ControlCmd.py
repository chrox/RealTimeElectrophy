# Commandline control of visual stimulation.
import logging
import VisionEgg.PyroClient

class StimCommand(object):
    def __init__(self, server_hostname='localhost', server_port=7766):
        self.server_hostname = server_hostname
        self.server_port = server_port

        self.pyro_client = VisionEgg.PyroClient.PyroClient(self.server_hostname,self.server_port)
        self.ephys_server = self.pyro_client.get("ephys_server")
        self.ephys_server.first_connection()
        
    def run(self, filename, left_params=None, right_params=None, assignments=[]):
        """
            Two ways to set stimulus params in runtime.
            i)  sending parameters for left/right viewport directly to ephys server
            ii) modifying parameters in script code
            Note that the second one has higher priority.
        """
        logger = logging.getLogger('StimControl.ControlCmd')
        if left_params is not None:
            logger.info('Send stimulation parameter to left viewport.')
            self.ephys_server.send_stimulus_params('left', left_params)
        if right_params is not None:
            logger.info('Send stimulation parameter to right viewport.')
            self.ephys_server.send_stimulus_params('right', right_params)
        try:
            with open(filename) as source_file:
                source = source_file.read()
        except:
            logger.error('Cannot read stimulation source code.')
            return
        
        self.ephys_server.run_demoscript()
        self.ephys_server.build_AST(source,assignments)
        # breaking waiting loop
        self.ephys_server.set_quit_status(True)
        
    def get_params(self):
        return self.ephys_server.get_stimulus_params()
        
    def is_running(self):
        return self.ephys_server.is_running()
        
    def quit_server(self,dummy=None):
        self.ephys_server.set_quit_status(True)
        self.ephys_server.set_quit_server_status(True)
        self.connected = 0
            
if __name__ == '__main__':
    command = StimCommand()
    command.run('manbar.py', assignments=['p.flash = True'])
    #command.quit_server()