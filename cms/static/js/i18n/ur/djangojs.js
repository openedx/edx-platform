

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
    "%(sel)s of %(cnt)s selected": [
      "%(cnt)s \u0645\u06cc\u06ba \u0633\u06d2 %(sel)s \u0645\u0646\u062a\u062e\u0628 \u06a9\u06cc\u0627 \u06af\u06cc\u0627",
      "%(cnt)s \u0645\u06cc\u06ba \u0633\u06d2 %(sel)s \u0645\u0646\u062a\u062e\u0628 \u06a9\u06cc\u06d2 \u06af\u0626\u06d2"
    ],
    "6 a.m.": "6 \u0635",
    "Available %s": "\u062f\u0633\u062a\u06cc\u0627\u0628 %s",
    "Cancel": "\u0645\u0646\u0633\u0648\u062e \u06a9\u0631\u06cc\u06ba",
    "Choose a time": "\u0648\u0642\u062a \u0645\u0646\u062a\u062e\u0628 \u06a9\u0631\u06cc\u06ba",
    "Choose all": "\u0633\u0628 \u0645\u0646\u062a\u062e\u0628 \u06a9\u0631\u06cc\u06ba",
    "Chosen %s": "\u0645\u0646\u062a\u062e\u0628 \u0634\u062f\u06c1 %s",
    "Filter": "\u0686\u06be\u0627\u0646\u0679\u06cc\u06ba",
    "Hide": "\u0686\u06be\u067e\u0627\u0626\u06cc\u06ba",
    "Midnight": "\u0646\u0635\u0641 \u0631\u0627\u062a",
    "Noon": "\u062f\u0648\u067e\u06be\u0631",
    "Now": "\u0627\u0628",
    "Remove": "\u062e\u0627\u0631\u062c \u06a9\u0631\u06cc\u06ba",
    "Show": "\u062f\u06a9\u06be\u0627\u0626\u06cc\u06ba",
    "Today": "\u0627\u0653\u062c",
    "Tomorrow": "\u0627\u0653\u0626\u0646\u062f\u06c1 \u06a9\u0644",
    "Yesterday": "\u06af\u0632\u0634\u062a\u06c1 \u06a9\u0644",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0627\u0653\u067e \u0646\u06d2 \u0627\u06cc\u06a9 \u06a9\u0627\u0631\u0648\u0627\u0626\u06cc \u0645\u0646\u062a\u062e\u0628 \u06a9\u06cc \u06be\u06d2\u060c \u0627\u0648\u0631 \u0627\u0653\u067e \u0646\u06d2 \u0630\u0627\u062a\u06cc \u062e\u0627\u0646\u0648\u06ba \u0645\u06cc\u06ba \u06a9\u0648\u0626\u06cc \u062a\u0628\u062f\u06cc\u0644\u06cc \u0646\u06c1\u06cc\u06ba \u06a9\u06cc \u063a\u0627\u0644\u0628\u0627\u064b \u0627\u0653\u067e '\u062c\u0627\u0648\u0654' \u0628\u0679\u0646 \u062a\u0644\u0627\u0634 \u06a9\u0631 \u0631\u06be\u06d2 \u06be\u06cc\u06ba \u0628\u062c\u0627\u0626\u06d2 '\u0645\u062e\u0641\u0648\u0638 \u06a9\u0631\u06cc\u06ba' \u0628\u0679\u0646 \u06a9\u06d2\u06d4",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0627\u0653\u067e \u0646\u06d2 \u0627\u06cc\u06a9 \u06a9\u0627\u0631\u0648\u0627\u0626\u06cc \u0645\u0646\u062a\u062e\u0628 \u06a9\u06cc \u06be\u06d2 \u0644\u06cc\u06a9\u0646 \u0627\u0628\u06be\u06cc \u062a\u06a9 \u0627\u0653\u067e \u0646\u06d2 \u0630\u0627\u062a\u06cc \u062e\u0627\u0646\u0648\u06ba \u0645\u06cc\u06ba \u0627\u067e\u0646\u06cc \u062a\u0628\u062f\u06cc\u0644\u06cc\u0627\u06ba \u0645\u062d\u0641\u0648\u0638 \u0646\u06c1\u06cc\u06ba \u06a9\u06cc \u06c1\u06cc\u06ba \u0628\u0631\u0627\u06c1 \u0645\u06be\u0631\u0628\u0627\u0646\u06cc \u0645\u062d\u0641\u0648\u0637 \u06a9\u0631\u0646\u06d2 \u06a9\u06d2 \u0644\u0626\u06d2 OK \u067e\u0631 \u06a9\u0644\u06a9 \u06a9\u0631\u06cc\u06ba\u06d4 \u0627\u0653\u067e \u06a9\u0627\u0648\u0627\u0626\u06cc \u062f\u0648\u0628\u0627\u0631\u06c1 \u0686\u0644\u0627\u0646\u06d2 \u06a9\u06cc \u0636\u0631\u0648\u0631\u062a \u06be\u0648\u06af\u06cc\u06d4",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0627\u0653\u067e \u06a9\u06d2 \u067e\u0627\u0633 \u0630\u0627\u062a\u06cc \u0642\u0627\u0628\u0644 \u062a\u062f\u0648\u06cc\u0646 \u062e\u0627\u0646\u0648\u06ba \u0645\u06cc\u06ba \u063a\u06cc\u0631 \u0645\u062d\u0641\u0648\u0638 \u062a\u0628\u062f\u06cc\u0644\u06cc\u0627\u06ba \u0645\u0648\u062c\u0648\u062f \u06be\u06cc\u06ba\u06d4 \u0627\u06af\u0631 \u0627\u0653\u067e \u06a9\u0648\u0626\u06cc \u06a9\u0627\u0631\u0648\u0627\u0626\u06cc \u06a9\u0631\u06cc\u06ba \u06af\u06d2 \u062a\u0648 \u0627\u0653\u067e \u06a9\u06cc \u063a\u06cc\u0631 \u0645\u062d\u0641\u0648\u0638 \u062a\u0628\u062f\u06cc\u0644\u06cc\u0627\u06ba \u0636\u0627\u0626\u0639 \u06be\u0648 \u062c\u0627\u0626\u06cc\u06ba \u06af\u06cc\u06d4"
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

