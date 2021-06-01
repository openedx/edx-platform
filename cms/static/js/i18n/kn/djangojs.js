

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=0;
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "6 a.m.": "\u0cac\u0cc6\u0cb3\u0c97\u0cbf\u0ca8 \u0cec \u0c97\u0c82\u0c9f\u0cc6 ",
    "Available %s": "\u0cb2\u0cad\u0ccd\u0caf %s ",
    "Cancel": "\u0cb0\u0ca6\u0ccd\u0ca6\u0cc1\u0c97\u0cca\u0cb3\u0cbf\u0cb8\u0cbf",
    "Choose a time": "\u0cb8\u0cae\u0caf\u0cb5\u0cca\u0c82\u0ca6\u0ca8\u0ccd\u0ca8\u0cc1 \u0c86\u0cb0\u0cbf\u0cb8\u0cbf",
    "Choose all": "\u0c8e\u0cb2\u0ccd\u0cb2\u0cb5\u0ca8\u0ccd\u0ca8\u0cc2  \u0c86\u0caf\u0ccd\u0ca6\u0cc1\u0c95\u0cca\u0cb3\u0ccd\u0cb3\u0cbf",
    "Chosen %s": "%s \u0c86\u0caf\u0ccd\u0ca6\u0cc1\u0c95\u0cca\u0cb3\u0ccd\u0cb3\u0cb2\u0cbe\u0c97\u0cbf\u0ca6\u0cc6",
    "Filter": "\u0cb6\u0cca\u0cd5\u0ca7\u0c95",
    "Hide": "\u0cae\u0cb0\u0cc6\u0cae\u0cbe\u0ca1\u0cb2\u0cc1",
    "Midnight": "\u0cae\u0ca7\u0ccd\u0caf\u0cb0\u0cbe\u0ca4\u0ccd\u0cb0\u0cbf",
    "Noon": "\u0cae\u0ca7\u0ccd\u0caf\u0cbe\u0cb9\u0ccd\u0ca8",
    "Now": "\u0c88\u0c97",
    "Remove": "\u0ca4\u0cc6\u0c97\u0cc6\u0ca6\u0cc1 \u0cb9\u0cbe\u0c95\u0cbf",
    "Remove all": "\u0c8e\u0cb2\u0ccd\u0cb2\u0cbe \u0ca4\u0cc6\u0c97\u0cc6\u0ca6\u0cc1\u0cb9\u0cbe\u0c95\u0cbf",
    "Show": "\u0caa\u0ccd\u0cb0\u0ca6\u0cb0\u0ccd\u0cb6\u0ca8",
    "Today": "\u0c88 \u0ca6\u0cbf\u0ca8",
    "Tomorrow": "\u0ca8\u0cbe\u0cb3\u0cc6",
    "Yesterday": "\u0ca8\u0cbf\u0ca8\u0ccd\u0ca8\u0cc6",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0ca8\u0cbf\u0cd5\u0cb5\u0cc1 \u0caa\u0ccd\u0cb0\u0ca4\u0ccd\u0caf\u0cc6\u0cd5\u0c95 \u0ca4\u0cbf\u0ca6\u0ccd\u0ca6\u0cac\u0cb2\u0ccd\u0cb2 \u0c95\u0ccd\u0cb7\u0cc6\u0cd5\u0ca4\u0ccd\u0cb0\u0c97\u0cb3\u0cb2\u0ccd\u0cb2\u0cbf \u0cac\u0ca6\u0cb2\u0cbe\u0cb5\u0ca3\u0cc6 \u0c89\u0cb3\u0cbf\u0cb8\u0cbf\u0cb2\u0ccd\u0cb2. \u0ca8\u0cbf\u0cae\u0ccd\u0cae \u0c89\u0cb3\u0cbf\u0cb8\u0ca6 \u0cac\u0ca6\u0cb2\u0cbe\u0cb5\u0ca3\u0cc6\u0c97\u0cb3\u0cc1 \u0ca8\u0cbe\u0cb6\u0cb5\u0cbe\u0c97\u0cc1\u0ca4\u0ccd\u0ca4\u0cb5\u0cc6"
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
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d",
      "%m/%d/%Y %H:%M:%S",
      "%m/%d/%Y %H:%M:%S.%f",
      "%m/%d/%Y %H:%M",
      "%m/%d/%Y",
      "%m/%d/%y %H:%M:%S",
      "%m/%d/%y %H:%M:%S.%f",
      "%m/%d/%y %H:%M",
      "%m/%d/%y"
    ],
    "DATE_FORMAT": "j F Y",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%m/%d/%Y",
      "%m/%d/%y",
      "%b %d %Y",
      "%b %d, %Y",
      "%d %b %Y",
      "%d %b, %Y",
      "%B %d %Y",
      "%B %d, %Y",
      "%d %B %Y",
      "%d %B, %Y"
    ],
    "DECIMAL_SEPARATOR": ".",
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "j M Y",
    "THOUSAND_SEPARATOR": ",",
    "TIME_FORMAT": "h:i A",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
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

