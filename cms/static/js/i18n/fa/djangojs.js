

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n > 1);
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
      " %(sel)s \u0627\u0632 %(cnt)s \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0647\u200c\u0627\u0646\u062f",
      " %(sel)s \u0627\u0632 %(cnt)s \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0647\u200c\u0627\u0646\u062f"
    ],
    "6 a.m.": "\u06f6 \u0635\u0628\u062d",
    "6 p.m.": "\u06f6 \u0628\u0639\u062f\u0627\u0632\u0638\u0647\u0631",
    "April": "\u0622\u0648\u0631\u06cc\u0644",
    "August": "\u0622\u06af\u0648\u0633\u062a",
    "Available %s": "%s\u06cc \u0645\u0648\u062c\u0648\u062f",
    "Cancel": "\u0627\u0646\u0635\u0631\u0627\u0641",
    "Choose": "\u0627\u0646\u062a\u062e\u0627\u0628",
    "Choose a Date": "\u06cc\u06a9 \u062a\u0627\u0631\u06cc\u062e \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f",
    "Choose a Time": "\u06cc\u06a9 \u0632\u0645\u0627\u0646 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f",
    "Choose a time": "\u06cc\u06a9 \u0632\u0645\u0627\u0646 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f",
    "Choose all": "\u0627\u0646\u062a\u062e\u0627\u0628 \u0647\u0645\u0647",
    "Chosen %s": "%s \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0647",
    "Click to choose all %s at once.": "\u0628\u0631\u0627\u06cc \u0627\u0646\u062a\u062e\u0627\u0628 \u06cc\u06a9\u062c\u0627\u06cc \u0647\u0645\u0647\u0654 %s \u06a9\u0644\u06cc\u06a9 \u06a9\u0646\u06cc\u062f.",
    "Click to remove all chosen %s at once.": "\u0628\u0631\u0627\u06cc \u062d\u0630\u0641 \u06cc\u06a9\u062c\u0627\u06cc \u0647\u0645\u0647\u0654 %s\u06cc \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0647 \u06a9\u0644\u06cc\u06a9 \u06a9\u0646\u06cc\u062f.",
    "December": "\u062f\u0633\u0627\u0645\u0628\u0631",
    "February": "\u0641\u0648\u0631\u06cc\u0647",
    "Filter": "\u063a\u0631\u0628\u0627\u0644",
    "Hide": "\u067e\u0646\u0647\u0627\u0646 \u06a9\u0631\u062f\u0646",
    "January": "\u0698\u0627\u0646\u0648\u06cc\u0647",
    "July": "\u062c\u0648\u0644\u0627\u06cc",
    "June": "\u0698\u0648\u0626\u0646",
    "March": "\u0645\u0627\u0631\u0633",
    "May": "\u0645\u06cc",
    "Midnight": "\u0646\u06cc\u0645\u0647\u200c\u0634\u0628",
    "Noon": "\u0638\u0647\u0631",
    "Note: You are %s hour ahead of server time.": [
      "\u062a\u0648\u062c\u0647: \u0634\u0645\u0627 %s \u0633\u0627\u0639\u062a \u0627\u0632 \u0632\u0645\u0627\u0646 \u0633\u0631\u0648\u0631 \u062c\u0644\u0648 \u0647\u0633\u062a\u06cc\u062f.",
      "\u062a\u0648\u062c\u0647: \u0634\u0645\u0627 %s \u0633\u0627\u0639\u062a \u0627\u0632 \u0632\u0645\u0627\u0646 \u0633\u0631\u0648\u0631 \u062c\u0644\u0648 \u0647\u0633\u062a\u06cc\u062f."
    ],
    "Note: You are %s hour behind server time.": [
      "\u062a\u0648\u062c\u0647: \u0634\u0645\u0627 %s \u0633\u0627\u0639\u062a \u0627\u0632 \u0632\u0645\u0627\u0646 \u0633\u0631\u0648\u0631 \u0639\u0642\u0628 \u0647\u0633\u062a\u06cc\u062f.",
      "\u062a\u0648\u062c\u0647: \u0634\u0645\u0627 %s \u0633\u0627\u0639\u062a \u0627\u0632 \u0632\u0645\u0627\u0646 \u0633\u0631\u0648\u0631 \u0639\u0642\u0628 \u0647\u0633\u062a\u06cc\u062f."
    ],
    "November": "\u0646\u0648\u0627\u0645\u0628\u0631",
    "Now": "\u0627\u06a9\u0646\u0648\u0646",
    "October": "\u0627\u06a9\u062a\u0628\u0631",
    "Remove": "\u062d\u0630\u0641",
    "Remove all": "\u062d\u0630\u0641 \u0647\u0645\u0647",
    "September": "\u0633\u067e\u062a\u0627\u0645\u0628\u0631",
    "Show": "\u0646\u0645\u0627\u06cc\u0634",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u0627\u06cc\u0646 \u0644\u06cc\u0633\u062a%s \u0647\u0627\u06cc  \u062f\u0631 \u062f\u0633\u062a\u0631\u0633 \u0627\u0633\u062a. \u0634\u0645\u0627 \u0645\u0645\u06a9\u0646 \u0627\u0633\u062a \u0628\u0631\u062e\u06cc \u0627\u0632 \u0622\u0646\u0647\u0627 \u0631\u0627 \u062f\u0631 \u0645\u062d\u0644  \u0632\u06cc\u0631\u0627\u0646\u062a\u062e\u0627\u0628 \u0646\u0645\u0627\u06cc\u06cc\u062f \u0648 \u0633\u067e\u0633 \u0631\u0648\u06cc \"\u0627\u0646\u062a\u062e\u0627\u0628\" \u0628\u06cc\u0646 \u062f\u0648 \u062c\u0639\u0628\u0647 \u06a9\u0644\u06cc\u06a9 \u06a9\u0646\u06cc\u062f.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u0627\u06cc\u0646 \u0641\u0647\u0631\u0633\u062a %s \u0647\u0627\u06cc \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0647 \u0627\u0633\u062a. \u0634\u0645\u0627 \u0645\u0645\u06a9\u0646 \u0627\u0633\u062a \u0628\u0631\u062e\u06cc \u0627\u0632 \u0627\u0646\u062a\u062e\u0627\u0628 \u0622\u0646\u0647\u0627 \u0631\u0627 \u062f\u0631 \u0645\u062d\u0644 \u0632\u06cc\u0631 \u0648\u0627\u0631\u062f \u0646\u0645\u0627\u06cc\u06cc\u062f \u0648 \u0633\u067e\u0633 \u0631\u0648\u06cc \"\u062d\u0630\u0641\" \u062c\u0647\u062a \u062f\u0627\u0631 \u0628\u06cc\u0646 \u062f\u0648 \u062c\u0639\u0628\u0647 \u062d\u0630\u0641 \u0634\u062f\u0647 \u0627\u0633\u062a.",
    "Today": "\u0627\u0645\u0631\u0648\u0632",
    "Tomorrow": "\u0641\u0631\u062f\u0627",
    "Type into this box to filter down the list of available %s.": "\u0628\u0631\u0627\u06cc \u063a\u0631\u0628\u0627\u0644 \u0641\u0647\u0631\u0633\u062a %s\u06cc \u0645\u0648\u062c\u0648\u062f \u062f\u0631\u0648\u0646 \u0627\u06cc\u0646 \u062c\u0639\u0628\u0647 \u062a\u0627\u06cc\u067e \u06a9\u0646\u06cc\u062f.",
    "Yesterday": "\u062f\u06cc\u0631\u0648\u0632",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0634\u0645\u0627 \u0639\u0645\u0644\u06cc \u0631\u0627 \u0627\u0646\u062c\u0627\u0645 \u062f\u0627\u062f\u0647 \u0627\u06cc\u062f\u060c \u0648\u0644\u06cc \u062a\u063a\u06cc\u06cc\u0631\u06cc \u0627\u0646\u062c\u0627\u0645 \u0646\u062f\u0627\u062f\u0647 \u0627\u06cc\u062f. \u0627\u062d\u062a\u0645\u0627\u0644\u0627 \u062f\u0646\u0628\u0627\u0644 \u06a9\u0644\u06cc\u062f Go \u0628\u0647 \u062c\u0627\u06cc Save \u0645\u06cc\u06af\u0631\u062f\u06cc\u062f.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0634\u0645\u0627 \u06a9\u0627\u0631\u06cc \u0631\u0627 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0631\u062f\u0647 \u0627\u06cc\u062f\u060c \u0648\u0644\u06cc \u0647\u0646\u0648\u0632 \u062a\u063a\u06cc\u06cc\u0631\u0627\u062a \u0628\u0639\u0636\u06cc \u0641\u06cc\u0644\u062f \u0647\u0627 \u0631\u0627 \u0630\u062e\u06cc\u0631\u0647 \u0646\u06a9\u0631\u062f\u0647 \u0627\u06cc\u062f. \u0644\u0637\u0641\u0627 OK \u0631\u0627 \u0641\u0634\u0627\u0631 \u062f\u0647\u06cc\u062f \u062a\u0627 \u0630\u062e\u06cc\u0631\u0647 \u0634\u0648\u062f.\n\u0634\u0645\u0627 \u0628\u0627\u06cc\u062f \u0639\u0645\u0644\u06cc\u0627\u062a \u0631\u0627 \u062f\u0648\u0628\u0627\u0631\u0647 \u0627\u0646\u062c\u0627\u0645 \u062f\u0647\u06cc\u062f.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0634\u0645\u0627 \u062a\u063a\u06cc\u06cc\u0631\u0627\u062a\u06cc \u062f\u0631 \u0628\u0639\u0636\u06cc \u0641\u06cc\u0644\u062f\u0647\u0627\u06cc \u0642\u0627\u0628\u0644 \u062a\u063a\u06cc\u06cc\u0631 \u0627\u0646\u062c\u0627\u0645 \u062f\u0627\u062f\u0647 \u0627\u06cc\u062f. \u0627\u06af\u0631 \u06a9\u0627\u0631\u06cc \u0627\u0646\u062c\u0627\u0645 \u062f\u0647\u06cc\u062f\u060c  \u062a\u063a\u06cc\u06cc\u0631\u0627\u062a \u0627\u0632 \u062f\u0633\u062a \u062e\u0648\u0627\u0647\u0646\u062f \u0631\u0641\u062a",
    "one letter Friday\u0004F": "\u062c",
    "one letter Monday\u0004M": "\u062f",
    "one letter Saturday\u0004S": "\u0634",
    "one letter Sunday\u0004S": "\u06cc",
    "one letter Thursday\u0004T": "\u067e",
    "one letter Tuesday\u0004T": "\u0633",
    "one letter Wednesday\u0004W": "\u0686"
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
    "DATETIME_FORMAT": "j F Y\u060c \u0633\u0627\u0639\u062a G:i",
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
    "FIRST_DAY_OF_WEEK": 6,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "Y/n/j\u060c\u200f G:i",
    "SHORT_DATE_FORMAT": "Y/n/j",
    "THOUSAND_SEPARATOR": ",",
    "TIME_FORMAT": "G:i",
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

