#!/usr/bin/env python
"""Setup script for the RealTimeElectrophy distribution.
"""
# Copyright (C) 2010-2011 Huang Xin
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL).
import os,sys
from distutils.core import setup,Extension

build_DT = False

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

def include_subpackages(pakage):
    for dirpath, dirnames, filenames in os.walk(pakage):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))

root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

main_packages = ['Experimenter','SpikeRecord','StimControl']

packages = []
data_files = []
ext_modules = []
package_dir = {}
package_data = {}

for package in main_packages:
    include_subpackages(package)

# LightStim config file
package_dir['StimControl.LightStim'] = os.path.join('StimControl','LightStim')
package_data['StimControl.LightStim'] = ['LightStim.cfg','DT.c']

if build_DT and sys.platform == 'win32':
    ext_modules.append(Extension(name='DT', sources=['StimControl/LightStim/DT.c']))
else:
    package_data['StimControl.LightStim'].append('DT.pyd')

setup(
    name = "RealTimeElectrophy",
    version = "0.6.0",
    author = "Huang Xin",
    author_email = "hwangxin@hsc.pku.edu.cn",
    url = "http://vislab.hsc.pku.edu.cn/code/RealTimeElectrophy",
    license = "LGPL", # Lesser GNU Public License
    description = "programs for real time visual neurophysiological research",
    packages = packages,
    package_dir = package_dir,
    package_data = package_data,
    ext_modules = ext_modules,
    data_files = data_files,
    long_description = ("The RealTimeElectrophy is a collection of useful programs designed to simplify visual neurophysiology research.\n"
        "The Experimenter package lies in the central position of the routines. A experimenter controls the visual stimulator \n"
        "via StimControl and receives spikes data from SpikeRecord. Precise frame timing is done by StimControl which sends \n"
        "a sweepstamp trigger to the acquisition system for each screen sweep. Once the visual stimuli is synchronized with \n"
        "the spikes via Experimenter, preliminary data analysis can be performed in real time."),
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: C',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Utilities',
    ]
        )