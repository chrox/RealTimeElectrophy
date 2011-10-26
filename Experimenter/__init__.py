




import logging  # available in Python 2.3
import logging.handlers


############# Logging #############
logger = logging.getLogger('Experimenter')
logger.setLevel( logging.INFO )
log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
log_handler_stderr = logging.StreamHandler()
log_handler_stderr.setFormatter(log_formatter)
logger.addHandler(log_handler_stderr)