import logging

def get_logger(name):
    """
    Returns a default logger.
    logging.basicConfig does not render to the console
    """
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    log.addHandler(log_handler)
    return log
