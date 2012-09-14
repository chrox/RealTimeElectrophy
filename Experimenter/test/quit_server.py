#!/usr/bin/python
# QuitServer script
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.

if __name__ == '__main__':
    from StimControl.ControlCmd import StimCommand
    cmd = StimCommand('192.168.1.105', 7766)
    cmd.quit_server()
