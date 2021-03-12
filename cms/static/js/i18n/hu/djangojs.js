

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
      "%(sel)s/%(cnt)s kijel\u00f6lve",
      "%(sel)s/%(cnt)s kijel\u00f6lve"
    ],
    "6 a.m.": "Reggel 6 \u00f3ra",
    "6 p.m.": "Este 6 \u00f3ra",
    "April": "\u00e1prilis",
    "August": "augusztus",
    "Available %s": "El\u00e9rhet\u0151 %s",
    "Cancel": "M\u00e9gsem",
    "Choose": "V\u00e1laszt\u00e1s",
    "Choose a Date": "V\u00e1lassza ki a d\u00e1tumot",
    "Choose a Time": "V\u00e1lassza ki az id\u0151t",
    "Choose a time": "V\u00e1lassza ki az id\u0151t",
    "Choose all": "Mindet kijel\u00f6lni",
    "Chosen %s": "%s kiv\u00e1lasztva",
    "Click to choose all %s at once.": "Kattintson az \u00f6sszes %s kiv\u00e1laszt\u00e1s\u00e1hoz.",
    "Click to remove all chosen %s at once.": "Kattintson az \u00f6sszes %s elt\u00e1vol\u00edt\u00e1s\u00e1hoz.",
    "December": "december",
    "February": "febru\u00e1r",
    "Filter": "Sz\u0171r\u0151",
    "Hide": "Elrejt",
    "January": "janu\u00e1r",
    "July": "j\u00falius",
    "June": "j\u00fanius",
    "March": "m\u00e1rcius",
    "May": "m\u00e1jus",
    "Midnight": "\u00c9jf\u00e9l",
    "Noon": "D\u00e9l",
    "Note: You are %s hour ahead of server time.": [
      "Megjegyz\u00e9s: %s \u00f3r\u00e1val a szerverid\u0151 el\u0151tt j\u00e1rsz",
      "Megjegyz\u00e9s: %s \u00f3r\u00e1val a szerverid\u0151 el\u0151tt j\u00e1rsz"
    ],
    "Note: You are %s hour behind server time.": [
      "Megjegyz\u00e9s: %s \u00f3r\u00e1val a szerverid\u0151 m\u00f6g\u00f6tt j\u00e1rsz",
      "Megjegyz\u00e9s: %s \u00f3r\u00e1val a szerverid\u0151 m\u00f6g\u00f6tt j\u00e1rsz"
    ],
    "November": "november",
    "Now": "Most",
    "October": "okt\u00f3ber",
    "Remove": "Elt\u00e1vol\u00edt\u00e1s",
    "Remove all": "\u00d6sszes t\u00f6rl\u00e9se",
    "September": "szeptember",
    "Show": "Mutat",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Ez az el\u00e9rhet\u0151 %s list\u00e1ja. \u00dagy v\u00e1laszthat k\u00f6z\u00fcl\u00fck, hogy r\u00e1kattint az al\u00e1bbi dobozban, \u00e9s megnyomja a dobozok k\u00f6zti \"V\u00e1laszt\u00e1s\" nyilat.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Ez a kiv\u00e1lasztott %s list\u00e1ja. Elt\u00e1vol\u00edthat k\u00f6z\u00fcl\u00fck, ha r\u00e1kattint, majd a k\u00e9t doboz k\u00f6zti \"Elt\u00e1vol\u00edt\u00e1s\" ny\u00edlra kattint.",
    "Today": "Ma",
    "Tomorrow": "Holnap",
    "Type into this box to filter down the list of available %s.": "\u00cdrjon a mez\u0151be az el\u00e9rhet\u0151 %s sz\u0171r\u00e9s\u00e9hez.",
    "Yesterday": "Tegnap",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Kiv\u00e1lasztott egy m\u0171veletet, \u00e9s nem m\u00f3dos\u00edtott egyetlen mez\u0151t sem. Feltehet\u0151en a Mehet gombot keresi a Ment\u00e9s helyett.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Kiv\u00e1lasztott egy m\u0171veletet, de nem mentette az egyes mez\u0151kh\u00f6z kapcsol\u00f3d\u00f3 m\u00f3dos\u00edt\u00e1sait. Kattintson az OK gombra a ment\u00e9shez. \u00dajra kell futtatnia az m\u0171veletet.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "M\u00e9g el nem mentett m\u00f3dos\u00edt\u00e1sai vannak egyes szerkeszthet\u0151 mez\u0151k\u00f6n. Ha most futtat egy m\u0171veletet, akkor a m\u00f3dos\u00edt\u00e1sok elvesznek.",
    "one letter Friday\u0004F": "P",
    "one letter Monday\u0004M": "H",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "V",
    "one letter Thursday\u0004T": "C",
    "one letter Tuesday\u0004T": "K",
    "one letter Wednesday\u0004W": "S"
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
    "DATETIME_FORMAT": "Y. F j. H:i",
    "DATETIME_INPUT_FORMATS": [
      "%Y.%m.%d. %H:%M:%S",
      "%Y.%m.%d. %H:%M:%S.%f",
      "%Y.%m.%d. %H:%M",
      "%Y.%m.%d.",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "Y. F j.",
    "DATE_INPUT_FORMATS": [
      "%Y.%m.%d.",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "F j.",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "Y.m.d. H:i",
    "SHORT_DATE_FORMAT": "Y.m.d.",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "H:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M",
      "%H:%M:%S.%f"
    ],
    "YEAR_MONTH_FORMAT": "Y. F"
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

