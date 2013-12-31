from django.conf import settings

def use_read_replica_if_available(queryset):
    return queryset.using("read_replica") if "read_replica" in settings.DATABASES else queryset