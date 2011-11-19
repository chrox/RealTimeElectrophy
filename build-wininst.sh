#!/bin/sh

python setup.py bdist_wininst -p win32
python setup.py bdist --format=zip -p win32

