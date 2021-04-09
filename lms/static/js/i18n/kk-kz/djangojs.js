

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n!=1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "%(sel)s of %(cnt)s selected": [
      "%(cnt)s-\u04a3 %(sel)s-\u044b(\u0456) \u0442\u0430\u04a3\u0434\u0430\u043b\u0434\u044b",
      "%(cnt)s-\u04a3 %(sel)s-\u044b(\u0456) \u0442\u0430\u04a3\u0434\u0430\u043b\u0434\u044b"
    ],
    "6 a.m.": "06",
    "Available %s": "%s \u0431\u0430\u0440",
    "Cancel": "\u0411\u043e\u043b\u0434\u044b\u0440\u043c\u0430\u0443",
    "Choose a time": "\u0423\u0430\u049b\u044b\u0442\u0442\u044b \u0442\u0430\u04a3\u0434\u0430",
    "Filter": "\u0421\u04af\u0437\u0433\u0456\u0448",
    "Hide": "\u0416\u0430\u0441\u044b\u0440\u0443",
    "Midnight": "\u0422\u04af\u043d \u0436\u0430\u0440\u044b\u043c",
    "Noon": "\u0422\u0430\u043b\u0442\u04af\u0441",
    "Now": "\u049a\u0430\u0437\u0456\u0440",
    "Remove": "\u04e8\u0448\u0456\u0440\u0443(\u0436\u043e\u044e)",
    "Show": "\u041a\u04e9\u0440\u0441\u0435\u0442\u0443",
    "Today": "\u0411\u04af\u0433\u0456\u043d",
    "Tomorrow": "\u0415\u0440\u0442\u0435\u04a3",
    "Yesterday": "\u041a\u0435\u0448\u0435",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0421\u0456\u0437 \u0421\u0430\u049b\u0442\u0430\u0443 \u0431\u0430\u0442\u044b\u0440\u043c\u0430\u0441\u044b\u043d\u0430 \u049b\u0430\u0440\u0430\u0493\u0430\u043d\u0434\u0430, Go(\u0410\u043b\u0493\u0430) \u0431\u0430\u0442\u044b\u0440\u043c\u0430\u0441\u044b\u043d \u0456\u0437\u0434\u0435\u043f \u043e\u0442\u044b\u0440\u0493\u0430\u043d \u0431\u043e\u043b\u0430\u0440\u0441\u044b\u0437, \u0441\u0435\u0431\u0435\u0431\u0456 \u0435\u0448\u049b\u0430\u043d\u0434\u0430\u0439 \u04e9\u0437\u0433\u0435\u0440\u0456\u0441 \u0436\u0430\u0441\u0430\u043c\u0430\u0439, \u04d9\u0440\u0435\u043a\u0435\u0442 \u0436\u0430\u0441\u0430\u0434\u044b\u04a3\u044b\u0437.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0421\u0456\u0437 \u04e9\u0437 \u04e9\u0437\u0433\u0435\u0440\u0456\u0441\u0442\u0435\u0440\u0456\u04a3\u0456\u0437\u0434\u0456 \u0441\u0430\u049b\u0442\u0430\u043c\u0430\u0439, \u04d9\u0440\u0435\u043a\u0435\u0442 \u0436\u0430\u0441\u0430\u0434\u044b\u04a3\u044b\u0437. \u04e8\u0442\u0456\u043d\u0456\u0448, \u0441\u0430\u049b\u0442\u0430\u0443 \u04af\u0448\u0456\u043d \u041e\u041a \u0431\u0430\u0442\u044b\u0440\u043c\u0430\u0441\u044b\u043d \u0431\u0430\u0441\u044b\u04a3\u044b\u0437 \u0436\u04d9\u043d\u0435 \u04e9\u0437 \u04d9\u0440\u0435\u043a\u0435\u0442\u0456\u04a3\u0456\u0437\u0434\u0456 \u049b\u0430\u0439\u0442\u0430 \u0436\u0430\u0441\u0430\u043f \u043a\u04e9\u0440\u0456\u04a3\u0456\u0437. ",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0421\u0456\u0437\u0434\u0456\u04a3 \u0442\u04e9\u043c\u0435\u043d\u0434\u0435\u0433\u0456 \u04e9\u0437\u0433\u0435\u0440\u043c\u0435\u043b\u0456 \u0430\u043b\u0430\u04a3\u0434\u0430\u0440\u0434\u0430(fields) \u04e9\u0437\u0433\u0435\u0440\u0456\u0441\u0442\u0435\u0440\u0456\u04a3\u0456\u0437 \u0431\u0430\u0440. \u0415\u0433\u0435\u0440 \u0430\u0440\u0442\u044b\u049b \u04d9\u0440\u0435\u043a\u0435\u0442 \u0436\u0430\u0441\u0430\u0441\u0430\u04a3\u044b\u0437\u0431 \u0441\u0456\u0437 \u04e9\u0437\u0433\u0435\u0440\u0456\u0441\u0442\u0435\u0440\u0456\u04a3\u0456\u0437\u0434\u0456 \u0436\u043e\u0493\u0430\u043b\u0442\u0430\u0441\u044b\u0437."
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
    "DATE_FORMAT": "N j, Y",
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
    "MONTH_DAY_FORMAT": "F j",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "m/d/Y",
    "THOUSAND_SEPARATOR": ",",
    "TIME_FORMAT": "P",
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

