def get_default_time_display(dt, show_timezone=True):
    """
    Converts a datetime to a string representation. This is the default
    representation used in Studio and LMS.
    It is of the form "Apr 09, 2013 at 16:00" or "Apr 09, 2013 at 16:00 UTC",
    depending on the value of show_timezone.

    If None is passed in for dt, an empty string will be returned.
    The default value of show_timezone is True.
    """
    if dt is None:
        return ""
    timezone = ""
    if dt is not None and show_timezone:
        if dt.tzinfo is not None:
            try:
                timezone = " " + dt.tzinfo.tzname(dt)
            except NotImplementedError:
                timezone = dt.strftime('%z')
        else:
            timezone = " UTC"
    return dt.strftime("%b %d, %Y at %H:%M") + timezone
