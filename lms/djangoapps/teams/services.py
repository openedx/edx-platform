from __future__ import absolute_import


class TeamsService(object):
    def echo(self, thing):
        from . import api
        return api.echo(thing)
