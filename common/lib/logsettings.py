import os
import platform
import sys
from logging.handlers import SysLogHandler

LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


def get_logger_config(log_dir,
                      logging_env="no_env",
                      tracking_filename="tracking.log",
                      edx_filename="edx.log",
                      audit_filename="audit.log",
                      dev_env=False,
                      syslog_addr=None,
                      debug=False,
                      local_loglevel='INFO',
                      console_loglevel=None,
                      service_variant=None):

    """

    Return the appropriate logging config dictionary. You should assign the
    result of this to the LOGGING var in your settings. The reason it's done
    this way instead of registering directly is because I didn't want to worry
    about resetting the logging state if this is called multiple times when
    settings are extended.

    If dev_env is set to true logging will not be done via local rsyslogd,
    instead, tracking and application logs will be dropped in log_dir.

    "tracking_filename" and "edx_filename" are ignored unless dev_env
    is set to true since otherwise logging is handled by rsyslogd.

    """

    # Revert to INFO if an invalid string is passed in
    if local_loglevel not in LOG_LEVELS:
        local_loglevel = 'INFO'

    if console_loglevel is None or console_loglevel not in LOG_LEVELS:
        console_loglevel = 'DEBUG' if debug else 'INFO'

    if service_variant is None:
        # default to a blank string so that if SERVICE_VARIANT is not
        # set we will not log to a sub directory
        service_variant = ''

    hostname = platform.node().split(".")[0]
    syslog_format = ("[service_variant={service_variant}]"
                     "[%(name)s][env:{logging_env}] %(levelname)s "
                     "[{hostname}  %(process)d] [%(filename)s:%(lineno)d] "
                     "- %(message)s").format(service_variant=service_variant,
                                             logging_env=logging_env,
                                             hostname=hostname)

    handlers = ['console', 'local'] if debug else ['console',
                                                   'syslogger-remote', 'local']

    logger_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)s %(process)d '
                          '[%(name)s] %(filename)s:%(lineno)d - %(message)s',
            },
            'syslog_format': {'format': syslog_format},
            'raw': {'format': '%(message)s'},
        },
        'handlers': {
            'console': {
                'level': console_loglevel,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout,
            },
            'syslogger-remote': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': syslog_addr,
                'formatter': 'syslog_format',
            },
            'newrelic': {
                'level': 'ERROR',
                'class': 'newrelic_logging.NewRelicHandler',
                'formatter': 'raw',
            }
        },
        'loggers': {
            'tracking': {
                'handlers': ['tracking'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'audit': {
                'handlers': ['audit'],
                'level': 'DEBUG',
                'propagate': False,
            },
            '': {
                'handlers': handlers,
                'level': 'DEBUG',
                'propagate': False
            },
        }
    }

    if dev_env:
        tracking_file_loc = os.path.join(log_dir, tracking_filename)
        edx_file_loc = os.path.join(log_dir, edx_filename)
        audit_file_loc = os.path.join(log_dir, audit_filename)
        logger_config['handlers'].update({
            'local': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': local_loglevel,
                'formatter': 'standard',
                'filename': edx_file_loc,
                'maxBytes': 1024 * 1024 * 2,
                'backupCount': 5,
            },
            'tracking': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': tracking_file_loc,
                'formatter': 'raw',
                'maxBytes': 1024 * 1024 * 2,
                'backupCount': 5,
            },
            'audit': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': audit_file_loc,
                'formatter': 'standard',
                'maxBytes': 1024 * 1024 * 2,
                'backupCount': 5,
            },
        })
    else:
        # for production environments we will only
        # log INFO and up
        logger_config['loggers']['']['level'] = 'INFO'
        logger_config['handlers'].update({
            'local': {
                'level': local_loglevel,
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'formatter': 'syslog_format',
                'facility': SysLogHandler.LOG_LOCAL0,
            },
            'tracking': {
                'level': 'DEBUG',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'facility': SysLogHandler.LOG_LOCAL1,
                'formatter': 'raw',
            },
            'audit': {
                'level': 'DEBUG',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'facility': SysLogHandler.LOG_LOCAL2,
                'formatter': 'raw',
            },
        })

    return logger_config
