import Pyro
Pyro.config.PYRO_MOBILE_CODE = True
Pyro.config.PYRO_TRACELEVEL = 3
Pyro.config.PYRO_PICKLE_FORMAT = 1

from VisionEgg.PyroClient import PyroClient


from VisionEgg.Gratings import SinGrating2D
from VisionEgg.MoreStimuli import Target2D
from StimControl.LightStim.Core import DefaultScreen

dummy_screen = DefaultScreen(['control'])

grating = SinGrating2D()
target = Target2D()

client = PyroClient(server_hostname='localhost')
#quit_controller = client.get('quit_controller')
#time.sleep(5.0) # show for 5 seconds
#
#quit_controller.set_between_go_value(1)
#quit_controller.evaluate_now()
stimulus_pool = client.get('stimulus_pool')
stimulus_pool.add_stimulus(target)
stimulus_pool.add_stimulus(grating)

