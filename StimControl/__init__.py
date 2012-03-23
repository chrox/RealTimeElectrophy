# The Stimulation Controller package.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

import logging

logger = logging.getLogger('StimControl')
logger.setLevel( logging.INFO )
log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
log_handler_stderr = logging.StreamHandler()
log_handler_stderr.setFormatter(log_formatter)
logger.addHandler(log_handler_stderr)
