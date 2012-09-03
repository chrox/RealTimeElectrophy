# test experiment
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import numpy as np
from Experimenter.Experiments.Experiment import ExperimentConfig,Experiment
from Experimenter.Experiments.STAExperiment import RFCMappingExp

ExperimentConfig(data_base_dir='data_test',stim_server_host='192.168.1.105',new_cell=True)

p_left, p_right = Experiment().get_params()

for eye in np.random.permutation(['left','right']):
    if eye == 'left':
        RFCMappingExp(eye='left', params=p_left).run()
    if eye == 'right':
        RFCMappingExp(eye='right', params=p_right).run()