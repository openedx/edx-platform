"""
Wrapper for dog_stats_api, ensuring tags are valid.
See: http://help.datadoghq.com/customer/portal/questions/908720-api-guidelines
"""
from dogapi import dog_stats_api


def _clean_tags(tags):
    """
    Helper method that does the actual cleaning of tags for sending to statsd.
    1. Handles any type of tag - a plain string, UTF-8 binary, or a unicode
       string, and converts it to UTF-8 encoded bytestring needed by statsd.
    2. Escape pipe character - used by statsd as a field separator.
    3. Trim to 200 characters (DataDog API limitation)
    """
    def clean(tagstr):
        if isinstance(tagstr, str):
            return tagstr.replace('|', '_')[:200]
        return unicode(tagstr).replace('|', '_')[:200].encode("utf-8")
    return [clean(t) for t in tags]


def increment(metric_name, *args, **kwargs):
    """
    Wrapper around dog_stats_api.increment that cleans any tags used.
    """
    if "tags" in kwargs:
        kwargs["tags"] = _clean_tags(kwargs["tags"])
    dog_stats_api.increment(metric_name, *args, **kwargs)


def histogram(metric_name, *args, **kwargs):
    """
    Wrapper around dog_stats_api.histogram that cleans any tags used.
    """
    if "tags" in kwargs:
        kwargs["tags"] = _clean_tags(kwargs["tags"])
    dog_stats_api.histogram(metric_name, *args, **kwargs)


def timer(metric_name, *args, **kwargs):
    """
    Wrapper around dog_stats_api.timer that cleans any tags used.
    """
    if "tags" in kwargs:
        kwargs["tags"] = _clean_tags(kwargs["tags"])
    return dog_stats_api.timer(metric_name, *args, **kwargs)
