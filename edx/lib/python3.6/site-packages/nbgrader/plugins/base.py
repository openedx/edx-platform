from traitlets.config import LoggingConfigurable


class BasePlugin(LoggingConfigurable):

    def __init__(self, **kwargs):
        super(BasePlugin, self).__init__(**kwargs)
