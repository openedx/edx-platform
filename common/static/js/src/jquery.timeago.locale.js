jQuery.timeago.settings.strings = {
    // Translators: %s will be a time quantity, such as "4 minutes" or "1 day"
    formatAgo: gettext("%s ago"),
    // Translators: %s will be a time quantity, such as "4 minutes" or "1 day"
    formatFromNow: gettext("%s from now"),
    seconds: gettext("less than a minute"),
    minute: gettext("about a minute"),
    minutes: function(value) { return ngettext("%d minute", "%d minutes", value)},
    hour: gettext("about an hour"),
    hours: function(value) { return ngettext("about %d hour", "about %d hours", value) },
    day: gettext("a day"),
    days: function(value) { return ngettext("%d day", "%d days", value) },
    month: gettext("about a month"),
    months: function(value) { return ngettext("%d month", "%d months", value) },
    year: gettext("about a year"),
    years: function(value) { return ngettext("%d year", "%d years", value) },
    numbers: []
};
