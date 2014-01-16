jQuery.timeago.settings.strings = {
    prefixAgo: pgettext("Prefix indicating time ago", ""),
    prefixFromNow: pgettext("Prefix indicating time from now", ""),
    suffixAgo: pgettext("Suffix indicating time ago", "ago"),
    suffixFromNow: pgettext("Suffix indicating time from now", "from now"),
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
    wordSeparator: pgettext("Word separator", " "),
    numbers: []
};
