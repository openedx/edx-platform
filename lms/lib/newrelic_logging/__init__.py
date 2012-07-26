import newrelic.agent

import logging


class NewRelicHandler(logging.Handler):
    def emit(self, record):
        if record.exc_info is not None:
            params = record.__dict__
            params['log_message'] = record.getMessage()

            newrelic.agent.record_exception(
                *record.exc_info,
                params=params
            )
