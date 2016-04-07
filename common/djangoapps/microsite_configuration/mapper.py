"""Maps a request to a tenant using the first part of the hostname.

For example:
  foo.example.com:8000 -> foo
  bar.baz.example.com -> bar

This is a simple example; you should probably verify tenant names
are valid before returning them, since the returned tenant name will
be issued in a `USE` SQL query.
"""

from db_multitenant import mapper


class SimpleTenantMapper(mapper.TenantMapper):
    def get_tenant_name(self, request):
        """Takes the first part of the hostname as the tenant"""
        hostname = request.get_host().split(':')[0].lower()
        return hostname.split('.')[0]

    def get_dbname(self, request):
        return self.get_tenant_name(request)

    def get_cache_prefix(self, request):
        return self.get_tenant_name(request)
