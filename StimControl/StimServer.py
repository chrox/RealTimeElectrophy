# Stimulation server extended from VisionEgg.PyroApps.EPhysServer

from distutils.version import LooseVersion as V
import ast
import Pyro
import pickle
import VisionEgg
import VisionEgg.PyroApps.EPhysServer as server
from StimControl import LightStim
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
        
def start_server( server_modules, server_class=RTEPhysServer ):
    pyro_server = NewPyroServer()
    #pyro_server = VisionEgg.PyroHelpers.PyroServer()
    default_viewports = ['control','left','right']
    DefaultScreen(default_viewports)
    screen = DefaultScreen.screen
    
    perspective_viewport = VisionEgg.Core.Viewport(screen=screen)
    overlay2D_viewport = VisionEgg.Core.Viewport(screen=screen)
    p = VisionEgg.FlowControl.Presentation(viewports=[perspective_viewport, overlay2D_viewport]) # 2D overlay on top
    #print 'main Presentation',p
    control_viewport_width = LightStim.config.get_viewport_width_pix('control')
    wait_text = VisionEgg.Text.Text(
        text = "Starting up...",
        position = (control_viewport_width/2.0,5),
        anchor='bottom',
        color = (1.0,0.0,0.0,0.0))


    overlay2D_viewport.parameters.stimuli = [wait_text]
    p.between_presentations() # draw wait_text

    ephys_server = server_class(p, server_modules)
    pyro_server.connect(ephys_server,"ephys_server")
    hostname,port = pyro_server.get_hostname_and_port()

    wait_text.parameters.text = "Waiting for connection at %s port %d"%(hostname,port)

    # get listener controller and register it
    p.add_controller(None,None, pyro_server.create_listener_controller())

    p.run_forever() # run until we get first connnection, which breaks out immmediately

    wait_text.parameters.text = "Loading new experiment, please wait."

    while not ephys_server.quit_server_status():
        # this flow control configuration SEEMS to be stable for
        # contiguously loaded scripts more rigorous testing would be
        # appreciated
        if not DefaultScreen.viewports == default_viewports:
            DefaultScreen.screen.close()
            DefaultScreen(default_viewports)
            screen = DefaultScreen.screen

        if ephys_server.get_stimkey() == "dropin_server":
            wait_text.parameters.text = "Vision Egg script mode"
            p.parameters.enter_go_loop = False
            # wait for client side quit status
            p.run_forever()
            if ephys_server.quit_server_status():
                break
            
            if ephys_server.exec_demoscript_flag:
                ephys_server.exec_AST(screen)

if __name__ == '__main__':
    start_server(server_modules, server_class=RTEPhysServer)