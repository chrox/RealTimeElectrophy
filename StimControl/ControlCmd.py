# Commandline control of visual stimulation.

import VisionEgg.PyroClient

class StimCommand(object):
    def __init__(self, server_hostname='localhost', server_port=7766):
        self.server_hostname = server_hostname
        self.server_port = server_port

        self.pyro_client = VisionEgg.PyroClient.PyroClient(self.server_hostname,self.server_port)
        self.ephys_server = self.pyro_client.get("ephys_server")
        self.ephys_server.first_connection()
        
    def run(self, filename, assignments=[]):
        source = open(filename).read()
        self.ephys_server.build_AST(source,assignments)
        self.ephys_server.run_demoscript()
        self.ephys_server.set_quit_status(True)
        
    def quit_server(self,dummy=None):
        self.ephys_server.set_quit_status(True)
        self.connected = 0
            
if __name__ == '__main__':
    command = StimCommand()
    command.run('manbar.py', assignments=['p.flash = True'])
    #command.quit_server()