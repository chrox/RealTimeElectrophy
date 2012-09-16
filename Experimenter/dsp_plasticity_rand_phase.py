# This is the main script to run disparity plasticity experiment.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import numpy as np
#from StimControl.LightStim.LightData import dictattr
from Experimenter.Experiments.Experiment import ExperimentConfig,Experiment,StimTimingExp,RestingExp
from Experimenter.Experiments.PSTHExperiment import ORITunExp,SPFTunExp,DSPTunExp,SpikeLatencyExp
from Experimenter.Experiments.STAExperiment import RFCMappingExp

ExperimentConfig(data_base_dir='data',stim_server_host='192.168.1.105',new_cell=False)

dummy_exp = Experiment()
p_left = dummy_exp.get_stimulus_params(eye='left')
p_right = dummy_exp.get_stimulus_params(eye='right')
"""
    Monocular tests
"""
# orientation tuning experiments find the optimal orientation for each eye
for eye in np.random.permutation(['left','right']):
    if eye == 'left':
        p_left.ori = ORITunExp(eye='left', params=None).run()
    if eye == 'right':
        p_right.ori = ORITunExp(eye='right', params=None).run()
        
# spatial frequency tuning experiments find the optimal spatial frequency
for eye in np.random.permutation(['left','right']):
    if eye == 'left':
        p_left.sfreqCycDeg = SPFTunExp(eye='left', params=p_left).run()
    if eye == 'right':
        p_right.sfreqCycDeg = SPFTunExp(eye='right', params=p_right).run()
        
# spiking latency experiments find the spike latency of the neuron
for eye in np.random.permutation(['left','right']):
    if eye == 'left':
        left_latency = SpikeLatencyExp(eye='left', params=p_left).run()
    if eye == 'right':
        right_latency = SpikeLatencyExp(eye='right', params=p_right).run()

intrinsic_delay = left_latency - right_latency
"""
    Induction and binocular tests
"""
intervals = np.random.permutation([-0.040, -0.016, -0.008, 0.0, 0.008, 0.016, 0.040])
intervals_rectified = intervals + intrinsic_delay
dsp_index = 1
for index,interval in enumerate(intervals_rectified):
    # interval string like m16ms(-0.016) or 24ms(0.024)
    interval_str = 'm'+str(int(intervals[index]*1000))+'ms' \
                    if interval-intrinsic_delay < 0 \
                    else str(int(intervals[index]*1000))+'ms'
    phase_str = 'rand'
    # receptive field mapping before induction
    exp_postfix = interval_str + '-' + phase_str + '-pre'
    for eye in np.random.permutation(['left','right']):
        if eye == 'left':
            p_left.xorigDeg, p_left.yorigDeg = RFCMappingExp(eye='left', params=p_left, 
                                                             postfix=exp_postfix).run()
        if eye == 'right':
            p_right.xorigDeg, p_right.yorigDeg = RFCMappingExp(eye='right', params=p_right, 
                                                               postfix=exp_postfix).run()
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
            p_left.xorigDeg, p_left.yorigDeg = RFCMappingExp(eye='left', params=p_left, 
															 postfix=exp_postfix).run()
        if eye == 'right':
            p_right.xorigDeg, p_right.yorigDeg = RFCMappingExp(eye='right', params=p_right, 
                                                               postfix=exp_postfix).run()
    
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
    