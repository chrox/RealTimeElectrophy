# This is the main script to run disparity plasticity experiment.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import numpy as np
#from StimControl.LightStim.LightData import dictattr
from Experimenter.Experiments.Experiment import ExperimentConfig,Experiment,StimTimingExp,RestingExp
from Experimenter.Experiments.PSTHExperiment import ORITunExp,SPFTunExp,DSPTunExp
from Experimenter.Experiments.STAExperiment import RFCMappingExp

ExperimentConfig(data_base_dir='data_test',stim_server_host='192.168.1.105',new_cell=True)

p_left, p_right = Experiment().get_params()

"""
    Monocular tests
"""
# orientation tuning experiments find the optimal orientation for each eye
for eye in np.random.permutation(['left','right']):
    if eye == 'left':
        p_left.ori = ORITunExp(eye='left', params=None).run()
        p_left.ori = 45.0
    if eye == 'right':
        p_right.ori = ORITunExp(eye='right', params=None).run()
        p_right.ori = 45.0
        
# spatial frequency tuning experiments find the optimal spatial frequency
for eye in np.random.permutation(['left','right']):
    if eye == 'left':
        p_left.sfreqCycDeg = SPFTunExp(eye='left', params=p_left).run()
        p_left.sfreqCycDeg = 0.55
    if eye == 'right':
        p_right.sfreqCycDeg = SPFTunExp(eye='right', params=p_right).run()
        p_right.sfreqCycDeg = 0.55

"""
    Induction and binocular tests
"""
intervals = [-0.040, -0.016, -0.008, 0.0, 0.008, 0.016, 0.040]
dsp_index = 1
for interval in np.random.permutation(intervals):
    # interval string like m16ms(-0.016) or 24ms(0.024)
    interval_str = 'm'+str(int(interval*1000))+'ms' if interval < 0 else str(int(interval*1000))+'ms'
    phase_str = 'rand'
    # receptive field mapping before induction
    exp_postfix = interval_str + '-' + phase_str + '-pre'
    for eye in np.random.permutation(['left','right']):
        if eye == 'left':
            RFCMappingExp(eye='left', params=p_left, postfix=exp_postfix).run()
            p_left.xorigDeg, p_left.yorigDeg = (-1.2, 1.5)
        if eye == 'right':
            RFCMappingExp(eye='right', params=p_right, postfix=exp_postfix).run()
            p_right.xorigDeg, p_right.yorigDeg = (1.6, 1.8)
    # disparity tuning experiment before induction
    exp_postfix = interval_str + '-' + phase_str + '-pre'
    pre_dsp = DSPTunExp(left_params=p_left,right_params=p_right,
                        repeats=4,postfix=exp_postfix).run()
    dsp_index += 1
    for times in range(3):
        # conditioning stimulus
        exp_postfix = interval_str + '-' + phase_str + '-' + str(times+1)
        StimTimingExp(left_phase=0, right_phase=0,
                      interval=interval, duration=3.0, postfix=exp_postfix, rand_phase=True).run()
        # short dsp tuning experiment
        if times < 2:
            exp_postfix = interval_str + '-' + phase_str + '-induction-' + str(times+1)
            short_dsp = DSPTunExp(left_params=p_left, right_params=p_right,
                                  repeats=1, postfix=exp_postfix).run()
    
    # disparity tuning experiment after induction
    exp_postfix = interval_str + '-' + phase_str + '-post'
    post_dsp = DSPTunExp(left_params=p_left, right_params=p_right, 
                         repeats=4, postfix=exp_postfix).run()
    # receptive field mapping after induction
    exp_postfix = interval_str + '-' + phase_str + '-post'
    for eye in np.random.permutation(['left','right']):
        if eye == 'left':
            p_left.xorigDeg, p_left.yorigDeg = RFCMappingExp(eye='left', params=p_left, postfix=exp_postfix).run()
        if eye == 'right':
            p_right.xorigDeg, p_right.yorigDeg = RFCMappingExp(eye='right', params=p_right, postfix=exp_postfix).run()
    
    for times in range(5):
        # resting experiment for 5min
        exp_postfix = interval_str + '-' + phase_str + '-' + str(times+1)
        RestingExp(duration=5.0, postfix=exp_postfix).run()
        if times < 4:
            # short dsp tuning experiment
            exp_postfix = interval_str + '-' + phase_str + '-recovery-' + str(times+1)
            short_dsp = DSPTunExp(left_params=p_left, right_params=p_right,
                                  repeats=1, postfix=exp_postfix).run()

    # disparity tuning experiment after resting
    exp_postfix = interval_str + '-' + phase_str + '-rest'
    rest_dsp = DSPTunExp(left_params=p_left, right_params=p_right, 
                         repeats=4, postfix=exp_postfix).run()
    RestingExp(duration=5.0, postfix=exp_postfix).run()