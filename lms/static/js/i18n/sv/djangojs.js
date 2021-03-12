

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
      "%(sel)s av %(cnt)s markerade",
      "%(sel)s av %(cnt)s markerade"
    ],
    "6 a.m.": "06:00",
    "6 p.m.": "6 p.m.",
    "April": "april",
    "August": "augusti",
    "Available %s": "Tillg\u00e4ngliga %s",
    "Cancel": "Avbryt",
    "Choose": "V\u00e4lj",
    "Choose a Date": "V\u00e4lj ett datum",
    "Choose a Time": "V\u00e4lj en tidpunkt",
    "Choose a time": "V\u00e4lj en tidpunkt",
    "Choose all": "V\u00e4lj alla",
    "Chosen %s": "V\u00e4lj %s",
    "Click to choose all %s at once.": "Klicka f\u00f6r att v\u00e4lja alla %s p\u00e5 en g\u00e5ng.",
    "Click to remove all chosen %s at once.": "Klicka f\u00f6r att ta bort alla valda %s p\u00e5 en g\u00e5ng.",
    "December": "december",
    "February": "februari",
    "Filter": "Filter",
    "Hide": "G\u00f6m",
    "January": "januari",
    "July": "juli",
    "June": "juni",
    "March": "mars",
    "May": "maj",
    "Midnight": "Midnatt",
    "Noon": "Middag",
    "Note: You are %s hour ahead of server time.": [
      "Notera: Du \u00e4r %s timme f\u00f6re serverns tid.",
      "Notera: Du \u00e4r %s timmar f\u00f6re serverns tid."
    ],
    "Note: You are %s hour behind server time.": [
      "Notera: Du \u00e4r %s timme efter serverns tid.",
      "Notera: Du \u00e4r %s timmar efter serverns tid."
    ],
    "November": "november",
    "Now": "Nu",
    "October": "oktober",
    "Remove": "Ta bort",
    "Remove all": "Ta bort alla",
    "September": "september",
    "Show": "Visa",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Detta \u00e4r listan med tillg\u00e4ngliga %s. Du kan v\u00e4lja ut vissa genom att markera dem i rutan nedan och sedan klicka p\u00e5 \"V\u00e4lj\"-knapparna mellan de tv\u00e5 rutorna.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Detta \u00e4r listan med utvalda %s. Du kan ta bort vissa genom att markera dem i rutan nedan och sedan klicka p\u00e5 \"Ta bort\"-pilen mellan de tv\u00e5 rutorna.",
    "Today": "I dag",
    "Tomorrow": "I morgon",
    "Type into this box to filter down the list of available %s.": "Skriv i denna ruta f\u00f6r att filtrera listan av tillg\u00e4ngliga %s.",
    "Yesterday": "I g\u00e5r",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Du har markerat en operation och du har inte gjort n\u00e5gra \u00e4ndringar i enskilda f\u00e4lt. Du letar antagligen efter Utf\u00f6r-knappen snarare \u00e4n Spara.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Du har markerat en operation, men du har inte sparat sparat dina \u00e4ndringar till enskilda f\u00e4lt \u00e4nnu. Var v\u00e4nlig klicka OK f\u00f6r att spara. Du kommer att beh\u00f6va k\u00f6ra operationen p\u00e5 nytt.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Du har \u00e4ndringar som inte sparats i enskilda redigerbara f\u00e4lt. Om du k\u00f6r en operation kommer de \u00e4ndringar som inte sparats att g\u00e5 f\u00f6rlorade.",
    "one letter Friday\u0004F": "F",
    "one letter Monday\u0004M": "M",
    "one letter Saturday\u0004S": "L",
    "one letter Sunday\u0004S": "S",
    "one letter Thursday\u0004T": "T",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "O"
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
    "DATETIME_FORMAT": "j F Y H:i",
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
      "%m/%d/%y"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "Y-m-d H:i",
    "SHORT_DATE_FORMAT": "Y-m-d",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "H:i",
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

