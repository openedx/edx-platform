

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
      "%(sel)s af %(cnt)s valgt",
      "%(sel)s af %(cnt)s valgt"
    ],
    "6 a.m.": "Klokken 6",
    "6 p.m.": "Klokken 18",
    "April": "April",
    "August": "August",
    "Available %s": "Tilg\u00e6ngelige %s",
    "Cancel": "Annuller",
    "Choose": "V\u00e6lg",
    "Choose a Date": "V\u00e6lg en Dato",
    "Choose a Time": "V\u00e6lg et Tidspunkt",
    "Choose a time": "V\u00e6lg et tidspunkt",
    "Choose all": "V\u00e6lg alle",
    "Chosen %s": "Valgte %s",
    "Click to choose all %s at once.": "Klik for at v\u00e6lge alle %s med det samme.",
    "Click to remove all chosen %s at once.": "Klik for at fjerne alle valgte %s med det samme.",
    "December": "December",
    "February": "Februar",
    "Filter": "Filtr\u00e9r",
    "Hide": "Skjul",
    "January": "Januar",
    "July": "Juli",
    "June": "Juni",
    "March": "Marts",
    "May": "Maj",
    "Midnight": "Midnat",
    "Noon": "Middag",
    "Note: You are %s hour ahead of server time.": [
      "Obs: Du er %s time forud i forhold til servertiden.",
      "Obs: Du er %s timer forud i forhold til servertiden."
    ],
    "Note: You are %s hour behind server time.": [
      "Obs: Du er %s time bagud i forhold til servertiden.",
      "Obs: Du er %s timer bagud i forhold til servertiden."
    ],
    "November": "November",
    "Now": "Nu",
    "October": "Oktober",
    "Remove": "Fjern",
    "Remove all": "Fjern alle",
    "September": "September",
    "Show": "Vis",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Dette er listen over tilg\u00e6ngelige %s. Du kan v\u00e6lge dem enkeltvis ved at markere dem i kassen nedenfor og derefter klikke p\u00e5 \"V\u00e6lg\"-pilen mellem de to kasser.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Dette er listen over valgte %s. Du kan fjerne dem enkeltvis ved at markere dem i kassen nedenfor og derefter klikke p\u00e5 \"Fjern\"-pilen mellem de to kasser.",
    "Today": "I dag",
    "Tomorrow": "I morgen",
    "Type into this box to filter down the list of available %s.": "Skriv i dette felt for at filtrere listen af tilg\u00e6ngelige %s.",
    "Yesterday": "I g\u00e5r",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Du har valgt en handling, og du har ikke udf\u00f8rt nogen \u00e6ndringer p\u00e5 felter. Det, du s\u00f8ger er formentlig Udf\u00f8r-knappen i stedet for Gem-knappen.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Du har valgt en handling, men du har ikke gemt dine \u00e6ndringer til et eller flere felter. Klik venligst OK for at gemme og v\u00e6lg dern\u00e6st handlingen igen.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Du har ugemte \u00e6ndringer af et eller flere redigerbare felter. Hvis du udf\u00f8rer en handling fra drop-down-menuen, vil du miste disse \u00e6ndringer.",
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
    "DATETIME_FORMAT": "j. F Y H:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j. F Y",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": ".",
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

