# Stimulation server extended from VisionEgg.PyroApps.EPhysServer

from distutils.version import LooseVersion as V
import os
import ast
import Pyro
import pickle
import logging
import pygame
import VisionEgg
import VisionEgg.PyroApps.EPhysServer as server
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr

from VisionEgg.PyroHelpers import PyroServer
from VisionEgg.PyroApps.DropinServer import DropinMetaController
from VisionEgg.PyroApps.DropinGUI import DropinMetaParameters

server_modules = [VisionEgg.PyroApps.DropinServer]

class MyDropinMetaController(DropinMetaController):
    def __init__(self,screen,presentation,stimuli):
        Pyro.core.ObjBase.__init__(self)
        self.meta_params = DropinMetaParameters()
        self.p = presentation

class Targets(object):
    def __init__(self, targets_list):
        self.targets = targets_list
    def __eq__(self,other):
        if len(self.targets)!=len(other.targets):
            return False
        for i in range(len(other.targets)):
            if not self.equal_target(self.targets[i],other.targets[i]):
                return False
        return True
    def equal_target(self, left, right):
        if isinstance(left, ast.Attribute) and isinstance(right, ast.Attribute):
            return self.equal_target(left.value, right.value) and left.attr == right.attr
        if isinstance(left, ast.Name) and isinstance(right, ast.Name):
            return left.id == right.id
        return False

class ModAssignments(ast.NodeTransformer):  
    def __init__(self, assign_exp):
        ast.NodeTransformer.__init__(self)
        self.new_assign = ast.parse(assign_exp).body[0]
    def visit_Assign(self, node):
        if Targets(node.targets) == Targets(self.new_assign.targets):
            node.value = self.new_assign.value
        return node

class RTEPhysServer(server.EPhysServer):
    """
        TODO: exec_AST should be interruptable from client side.
    """
    def __init__(self, *args,**kwargs):
        server.EPhysServer.__init__(self,*args,**kwargs)
        ### hacking here to suppress annoying prints in log ###
        self.stimdict['dropin_server'] = (MyDropinMetaController, self.stimdict['dropin_server'][1])
        #######################################################
        self.really_quit_server = False
        self.AST_tree_completed = False
        
        self.logpath = 'stimlog'
        if not os.path.exists(self.logpath):
            os.makedirs(self.logpath)
        
    def build_AST(self, source, assignments=[]):
        AST = ast.parse(source)
        for assign in assignments:
            AST = ModAssignments(assign).visit(AST)
        self.AST = AST
        self.AST_tree_completed = True
        
    def exec_AST(self, screen):
        code_module = compile(self.AST, '', 'exec')
        exec code_module in locals()
        if 'p' in locals() and isinstance(locals()['p'], VisionEgg.FlowControl.Presentation):
            presentation = locals()['p']
        elif 'sweep' in locals() and isinstance(locals()['sweep'], VisionEgg.FlowControl.Presentation):
            presentation = locals()['sweep']
        else:
            raise RuntimeError('Cannot find presentation instance in locals().')
        self.script_dropped_frames = presentation.were_frames_dropped_in_last_go_loop()
        self.presentation.last_go_loop_start_time_absolute_sec = presentation.last_go_loop_start_time_absolute_sec # evil hack...
        self.exec_demoscript_flag = False
        self.set_quit_status(False)
        
    def _set_parameters(self, dest_params, source_params):
        for paramname, paramval in source_params.items():
            setattr(dest_params, paramname, paramval)
        
    def is_AST_tree_completed(self):
        return self.AST_tree_completed
    
    def set_AST_tree_to_build(self):
        self.AST_tree_completed = False
        
    def get_stimulus_params(self):
        left_params = dictattr()
        right_params = dictattr()
        with open('stimulus_params.pkl','rb') as pkl_input:
            params = pickle.load(pkl_input)
            self._set_parameters(left_params, params['left'][0])
            self._set_parameters(right_params, params['right'][0])
        return (left_params, right_params)
        
    def send_stimulus_params(self, eye, params):
        try:
            with open('stimulus_params.pkl','rb') as pkl_input:
                preferences_dict = pickle.load(pkl_input)
            if eye not in preferences_dict:
                preferences_dict[eye] = [{}] * 2
            with open('stimulus_params.pkl','wb') as pkl_output:
                preferences_dict[eye][0].update(params)
                pickle.dump(preferences_dict, pkl_output)
        except:
            raise RuntimeError('Cannot save params for ' + eye + 'viewport.')
    
    def log_stimulus(self, exp_name):
        # logging stimulus
        logfile = self.logpath + os.path.sep + exp_name + '.log'
        log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
        log_handler_logfile = logging.FileHandler(logfile)
        log_handler_logfile.setFormatter(log_formatter)
        
        lightstim_logger = logging.getLogger('VisionEgg')
        lightstim_logger.setLevel( logging.INFO )
        lightstim_logger.addHandler(log_handler_logfile)
        
        lightstim_logger = logging.getLogger('LightStim')
        lightstim_logger.setLevel( logging.INFO )
        lightstim_logger.addHandler(log_handler_logfile)
        
        stimcontrol_logger = logging.getLogger('StimControl')
        stimcontrol_logger.setLevel( logging.INFO )
        stimcontrol_logger.addHandler(log_handler_logfile)
    
    def get_stimulus_log(self, exp_name):
        logfile = self.logpath + os.path.sep + exp_name + '.log'
        with open(logfile) as log:
            return log.readlines()
    
    def is_running(self):
        return self.exec_demoscript_flag
        
    def set_quit_server_status(self, status):
        self.really_quit_server = status
        
    def quit_server_status(self):
        return self.really_quit_server
        
    def quit_presentation(self):
        pass
    
class NewPyroServer(PyroServer):
    def __init__(self):
        Pyro.config.PYRO_MULTITHREADED = 1 # multithreading!
        PyroServer.__init__(self)
        
    def disconnect(self, _object):
        try:
            VERSION = Pyro.core.constants.VERSION
        except:
            VERSION = Pyro.constants.VERSION
        if V(VERSION) >= V('3.2'):
            self.daemon.disconnect(_object)
        else:
            # workaround bug in Pyro pre-3.2
            del self.daemon.implementations[_object.GUID()]
            _object.setDaemon(None)

class StimServer(object):
    def __init__(self):
        self.presentation = None
        self.ephys_server = None
        
    def start_server(self, server_modules=server_modules, server_class=RTEPhysServer ):
        pyro_server = NewPyroServer()
        default_viewports = ['left','right']
        DefaultScreen(default_viewports)
        screen = DefaultScreen.screen
        
        perspective_viewport = VisionEgg.Core.Viewport(screen=screen)
        overlay2D_viewport = VisionEgg.Core.Viewport(screen=screen)
        self.presentation = VisionEgg.FlowControl.Presentation(viewports=[perspective_viewport, overlay2D_viewport]) # 2D overlay on top
        self.presentation.parameters.handle_event_callbacks = [(pygame.locals.KEYDOWN, self.keydown_callback)]
        self.presentation.between_presentations() # draw wait_text
    
        self.ephys_server = server_class(self.presentation, server_modules)
        pyro_server.connect(self.ephys_server,"ephys_server")
    
        # get listener controller and register it
        self.presentation.add_controller(None,None, pyro_server.create_listener_controller())
    
        self.presentation.run_forever() # run until we get first connnection, which breaks out immmediately
    
        while not self.ephys_server.quit_server_status():
            if self.ephys_server.get_stimkey() == "dropin_server":
                self.presentation.parameters.enter_go_loop = False
                # wait for client side quit status
                self.presentation.run_forever()
                if self.ephys_server.quit_server_status():
                    break
                
                if self.ephys_server.exec_demoscript_flag:
                    self.ephys_server.exec_AST(screen)
      
    def keydown_callback(self,event):
        if event.key == pygame.locals.K_q:
            self.presentation.parameters.quit = True
            self.ephys_server.set_quit_server_status(True)
          
if __name__ == '__main__':
    #start_server(server_modules, server_class=RTEPhysServer)
    stim_server = StimServer()
    stim_server.start_server()