

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n != 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "6 a.m.": "\u09ec \u09aa\u09c2\u09b0\u09cd\u09ac\u09be\u09b9\u09cd\u09a8",
    "Available %s": "%s \u09ac\u09bf\u09a6\u09cd\u09af\u09ae\u09be\u09a8",
    "Cancel": "\u09ac\u09be\u09a4\u09bf\u09b2",
    "Choose": "\u09ac\u09be\u099b\u09be\u0987 \u0995\u09b0\u09c1\u09a8",
    "Choose a time": "\u09b8\u09ae\u09df \u09a8\u09bf\u09b0\u09cd\u09ac\u09be\u099a\u09a8 \u0995\u09b0\u09c1\u09a8",
    "Choose all": "\u09b8\u09ac \u09ac\u09be\u099b\u09be\u0987 \u0995\u09b0\u09c1\u09a8",
    "Chosen %s": "%s \u09ac\u09be\u099b\u09be\u0987 \u0995\u09b0\u09be \u09b9\u09df\u09c7\u099b\u09c7",
    "Click to choose all %s at once.": "\u09b8\u09ac %s \u098f\u0995\u09ac\u09be\u09b0\u09c7 \u09ac\u09be\u099b\u09be\u0987 \u0995\u09b0\u09be\u09b0 \u099c\u09a8\u09cd\u09af \u0995\u09cd\u09b2\u09bf\u0995 \u0995\u09b0\u09c1\u09a8\u0964",
    "Filter": "\u09ab\u09bf\u09b2\u09cd\u099f\u09be\u09b0",
    "Hide": "\u09b2\u09c1\u0995\u09be\u09a8",
    "Midnight": "\u09ae\u09a7\u09cd\u09af\u09b0\u09be\u09a4",
    "Noon": "\u09a6\u09c1\u09aa\u09c1\u09b0",
    "Note: You are %s hour ahead of server time.": [
      "\u09a8\u09cb\u099f: \u0986\u09aa\u09a8\u09bf \u09b8\u09be\u09b0\u09cd\u09ad\u09be\u09b0 \u09b8\u09ae\u09df\u09c7\u09b0 \u099a\u09c7\u09df\u09c7 %s \u0998\u09a8\u09cd\u099f\u09be \u09b8\u09be\u09ae\u09a8\u09c7 \u0986\u099b\u09c7\u09a8\u0964",
      "\u09a8\u09cb\u099f: \u0986\u09aa\u09a8\u09bf \u09b8\u09be\u09b0\u09cd\u09ad\u09be\u09b0 \u09b8\u09ae\u09df\u09c7\u09b0 \u099a\u09c7\u09df\u09c7 %s \u0998\u09a8\u09cd\u099f\u09be \u09b8\u09be\u09ae\u09a8\u09c7 \u0986\u099b\u09c7\u09a8\u0964"
    ],
    "Note: You are %s hour behind server time.": [
      "\u09a8\u09cb\u099f: \u0986\u09aa\u09a8\u09bf \u09b8\u09be\u09b0\u09cd\u09ad\u09be\u09b0 \u09b8\u09ae\u09df\u09c7\u09b0 \u099a\u09c7\u09df\u09c7 %s \u0998\u09a8\u09cd\u099f\u09be \u09aa\u09c7\u099b\u09a8\u09c7 \u0986\u099b\u09c7\u09a8\u0964",
      "\u09a8\u09cb\u099f: \u0986\u09aa\u09a8\u09bf \u09b8\u09be\u09b0\u09cd\u09ad\u09be\u09b0 \u09b8\u09ae\u09df\u09c7\u09b0 \u099a\u09c7\u09df\u09c7 %s \u0998\u09a8\u09cd\u099f\u09be \u09aa\u09c7\u099b\u09a8\u09c7 \u0986\u099b\u09c7\u09a8\u0964"
    ],
    "Now": "\u098f\u0996\u09a8",
    "Remove": "\u09ae\u09c1\u099b\u09c7 \u09ab\u09c7\u09b2\u09c1\u09a8",
    "Remove all": "\u09b8\u09ac \u09ae\u09c1\u099b\u09c7 \u09ab\u09c7\u09b2\u09c1\u09a8",
    "Show": "\u09a6\u09c7\u0996\u09be\u09a8",
    "Today": "\u0986\u099c",
    "Tomorrow": "\u0986\u0997\u09be\u09ae\u09c0\u0995\u09be\u09b2",
    "Yesterday": "\u0997\u09a4\u0995\u09be\u09b2"
  };
  for (var key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      var value = django.catalog[msgid];
      if (typeof(value) == 'undefined') {
        return msgid;
      } else {
        return (typeof(value) == 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      var value = django.catalog[singular];
      if (typeof(value) == 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      var value = django.gettext(context + '\x04' + msgid);
      if (value.indexOf('\x04') != -1) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.indexOf('\x04') != -1) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {
    "DATETIME_FORMAT": "N j, Y, P",
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j F, Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%d-%m-%Y",
      "%d-%m-%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ".",
    "FIRST_DAY_OF_WEEK": 6,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "j M, Y",
    "THOUSAND_SEPARATOR": ",",
    "TIME_FORMAT": "g:i A",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M",
      "%H:%M:%S.%f"
    ],
    "YEAR_MONTH_FORMAT": "F Y"
  };

    django.get_format = function(format_type) {
      var value = django.formats[format_type];
      if (typeof(value) == 'undefined') {
        return format_type;
      } else {
        return value;
      }
    };

    /* add to global namespace */
    globals.pluralidx = django.pluralidx;
    globals.gettext = django.gettext;
    globals.ngettext = django.ngettext;
    globals.gettext_noop = django.gettext_noop;
    globals.pgettext = django.pgettext;
    globals.npgettext = django.npgettext;
    globals.interpolate = django.interpolate;
    globals.get_format = django.get_format;

    django.jsi18n_initialized = true;
  }

}(this));

