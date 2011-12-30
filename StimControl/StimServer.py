# Stimulation server extended from VisionEgg.PyroApps.EPhysServer

from distutils.version import LooseVersion as V
import Pyro
import VisionEgg
import VisionEgg.PyroApps.EPhysServer as server
import VisionEgg.PyroApps.AST_ext as AST_ext
from StimControl import LightStim
from StimControl.LightStim.Core import DefaultScreen

from VisionEgg.PyroHelpers import PyroServer
from VisionEgg.PyroApps.ScreenPositionServer import ScreenPositionMetaController
from VisionEgg.PyroApps.ScreenPositionGUI import ScreenPositionParameters

server_modules = [VisionEgg.PyroApps.DropinServer]

class RTEPhysServer(server.EPhysServer):
    def exec_AST(self, screen, dropin_meta_params):
        if dropin_meta_params.vars_list is not None:
            for var in dropin_meta_params.vars_list:
                self.AST = AST_ext.modify_AST(self.AST, var[0], var[1])

        code_module = self.AST.compile()
        exec code_module in locals()
        if isinstance(locals()['p'], VisionEgg.FlowControl.Presentation):
            presentation = locals()['p']
        elif isinstance(locals()['sweep'], VisionEgg.FlowControl.Presentation):
            presentation = locals()['sweep']
        self.script_dropped_frames = presentation.were_frames_dropped_in_last_go_loop()
        self.presentation.last_go_loop_start_time_absolute_sec = presentation.last_go_loop_start_time_absolute_sec # evil hack...
        self.exec_demoscript_flag = False
        
class NewPyroServer(PyroServer):
    def disconnect(self,object):
        try:
            VERSION = Pyro.core.constants.VERSION
        except:
            VERSION = Pyro.constants.VERSION
        if V(VERSION) >= V('3.2'):
            self.daemon.disconnect(object)
        else:
            # workaround bug in Pyro pre-3.2
            del self.daemon.implementations[object.GUID()]
            object.setDaemon(None)
        
def start_server( server_modules, server_class=RTEPhysServer ):
    loadNewExpr = True
    pyro_server = NewPyroServer()
    #pyro_server = VisionEgg.PyroHelpers.PyroServer()
    default_viewports = ['control','left','right']
    DefaultScreen(default_viewports)
    screen = DefaultScreen.screen
    
    temp = ScreenPositionParameters()

    projection = VisionEgg.Core.PerspectiveProjection(temp.left,
                                                      temp.right,
                                                      temp.bottom,
                                                      temp.top,
                                                      temp.near,
                                                      temp.far)
    perspective_viewport = VisionEgg.Core.Viewport(screen=screen, projection=projection)
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

    # now hand over control of projection to ScreenPositionMetaController
    projection_controller = ScreenPositionMetaController(p,projection)
    pyro_server.connect(projection_controller,"projection_controller")

    ephys_server = server_class(p, server_modules)
    pyro_server.connect(ephys_server,"ephys_server")
    hostname,port = pyro_server.get_hostname_and_port()

    wait_text.parameters.text = "Waiting for connection at %s port %d"%(hostname,port)

    # get listener controller and register it
    p.add_controller(None,None, pyro_server.create_listener_controller())

    p.run_forever() # run until we get first connnection, which breaks out immmediately

    wait_text.parameters.text = "Loading new experiment, please wait."

    while not ephys_server.get_quit_status():
        # this flow control configuration SEEMS to be stable for
        # contiguously loaded scripts more rigorous testing would be
        # appreciated
        if not DefaultScreen.viewports == default_viewports:
            DefaultScreen.screen.close()
            DefaultScreen(default_viewports)
            screen = DefaultScreen.screen
        if loadNewExpr:
            wait_text.parameters.text = "Loading new experiment, please wait."
            perspective_viewport.parameters.stimuli = []
            overlay2D_viewport.parameters.stimuli = [wait_text]
            p.between_presentations() # draw wait_text
            pyro_name, meta_controller_class, stimulus_list = ephys_server.get_next_stimulus_meta_controller()
            stimulus_meta_controller = meta_controller_class(screen, p, stimulus_list) # instantiate meta_controller
            pyro_server.connect(stimulus_meta_controller, pyro_name)

        if ephys_server.get_stimkey() == "dropin_server":
            wait_text.parameters.text = "Vision Egg script mode"

            p.parameters.enter_go_loop = False
            p.parameters.quit = False
            p.run_forever()

            # At this point quit signal was sent by client to either:

            # 1) Execute the script (ie. "exec_demoscript_flag" has
            # been set)

            # 2) Load a DIFFERENT script ("loadNewExpr" should be set
            # to False in this event)

            # 3) Load a BUILT IN experiment ("loadNewExpr" should be
            # set to True in this event)

            if ephys_server.exec_demoscript_flag:
                dropin_meta_params = stimulus_meta_controller.get_parameters()
                ephys_server.exec_AST(screen, dropin_meta_params)

            if ephys_server.get_stimkey() == "dropin_server":
                # Either:
                # 1) Same script (just finished executing)
                # 2) Loading a new script
                loadNewExpr = False
            else:
                # 3) load a BUILT IN experiment
                pyro_server.disconnect(stimulus_meta_controller)
                del stimulus_meta_controller # we have to do this explicitly because Pyro keeps a copy of the reference
                loadNewExpr = True
        else:
            overlay2D_viewport.parameters.stimuli = [] # clear wait_text
            for stim in stimulus_list:
                if stim[0] == '3d_perspective':
                    perspective_viewport.parameters.stimuli.append(stim[1])
                elif stim[0] == '3d_perspective_with_set_viewport_callback':
                    _key, stimulus, callback_function = stim
                    callback_function(perspective_viewport)
                    perspective_viewport.parameters.stimuli.append(stimulus)
                elif stim[0] == '2d_overlay':
                    overlay2D_viewport.parameters.stimuli.append(stim[1])
                else:
                    raise RuntimeError("Unknown viewport id %s"%stim[0])

            # enter loop
            p.parameters.enter_go_loop = False
            p.parameters.quit = False
            p.run_forever()

            # At this point quit signal was sent by client to either:

            # 1) Load a script ("loadNewExpr" should be set to 1 in
            # this event)

            # 2) Load a BUILT IN experiment ("loadNewExpr" should be
            # set to 1 in this event)

            pyro_server.disconnect(stimulus_meta_controller)
            del stimulus_meta_controller # we have to do this explicitly because Pyro keeps a copy of the reference

if __name__ == '__main__':
    start_server(server_modules, server_class=RTEPhysServer)