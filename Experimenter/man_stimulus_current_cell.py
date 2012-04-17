# Manual stimulus used to find the receptive field position and size.
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from Experiments.Experiment import ExperimentConfig,ManbarExp,MangratingExp

ExperimentConfig(data_base_dir='data',exp_base_dir='Experiments',new_cell=False)

# When a neuron is isolated in Plexon PlexControl software. The experimenter should choose proper
# bar to estimate the size and position of the receptive field of that neuron.
p_left, p_right = ManbarExp(left_params=None, right_params=None).run()
# The bar parameter is passed to mangrating and proper spatial frequency and orientation should be choosed.
p_left, p_right = MangratingExp(left_params=None, right_params=None).run()