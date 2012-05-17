import newrelic.agent
import sys

def record_exception(logger, msg, params={}, ignore_errors=[]):
    logger.exception(msg)
    newrelic.agent.record_exception(*sys.exc_info())

