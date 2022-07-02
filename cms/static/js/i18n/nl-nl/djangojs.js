

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n != 1);
    if (typeof v === 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  const newcatalog = {
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s van de %(cnt)s geselecteerd",
      "%(sel)s van de %(cnt)s geselecteerd"
    ],
    "6 a.m.": "6 uur 's ochtends",
    "6 p.m.": "6 uur 's avonds",
    "April": "april",
    "August": "augustus",
    "Available %s": "Beschikbare %s",
    "Cancel": "Annuleren",
    "Choose": "Kiezen",
    "Choose a Date": "Kies een datum",
    "Choose a Time": "Kies een tijdstip",
    "Choose a time": "Kies een tijd",
    "Choose all": "Alle kiezen",
    "Chosen %s": "Gekozen %s",
    "Click to choose all %s at once.": "Klik om alle %s te kiezen.",
    "Click to remove all chosen %s at once.": "Klik om alle gekozen %s tegelijk te verwijderen.",
    "December": "december",
    "February": "februari",
    "Filter": "Filter",
    "Hide": "Verbergen",
    "January": "januari",
    "July": "juli",
    "June": "juni",
    "March": "maart",
    "May": "mei",
    "Midnight": "Middernacht",
    "Noon": "12 uur 's middags",
    "Note: You are %s hour ahead of server time.": [
      "Let op: u ligt %s uur voor ten opzichte van de servertijd.",
      "Let op: u ligt %s uur voor ten opzichte van de servertijd."
    ],
    "Note: You are %s hour behind server time.": [
      "Let op: u ligt %s uur achter ten opzichte van de servertijd.",
      "Let op: u ligt %s uur achter ten opzichte van de servertijd."
    ],
    "November": "november",
    "Now": "Nu",
    "October": "oktober",
    "Remove": "Verwijderen",
    "Remove all": "Alle verwijderen",
    "September": "september",
    "Show": "Tonen",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Dit is de lijst met beschikbare %s. U kunt er een aantal kiezen door ze in het vak hieronder te selecteren en daarna op de pijl 'Kiezen' tussen de twee vakken te klikken.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Dit is de lijst met gekozen %s. U kunt er een aantal verwijderen door ze in het vak hieronder te selecteren en daarna op de pijl 'Verwijderen' tussen de twee vakken te klikken.",
    "Today": "Vandaag",
    "Tomorrow": "Morgen",
    "Type into this box to filter down the list of available %s.": "Typ in dit vak om de lijst met beschikbare %s te filteren.",
    "Yesterday": "Gisteren",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "U hebt een actie geselecteerd, en geen wijzigingen in afzonderlijke velden aangebracht. Waarschijnlijk zoekt u de knop Gaan in plaats van de knop Opslaan.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "U hebt een actie geselecteerd, maar uw wijzigingen in afzonderlijke velden nog niet opgeslagen. Klik op OK om deze op te slaan. U dient de actie opnieuw uit te voeren.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "U hebt niet-opgeslagen wijzigingen op afzonderlijke bewerkbare velden. Als u een actie uitvoert, gaan uw wijzigingen verloren.",
    "one letter Friday\u0004F": "V",
    "one letter Monday\u0004M": "M",
    "one letter Saturday\u0004S": "Z",
    "one letter Sunday\u0004S": "Z",
    "one letter Thursday\u0004T": "D",
    "one letter Tuesday\u0004T": "D",
    "one letter Wednesday\u0004W": "W"
  };
  for (const key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      const value = django.catalog[msgid];
      if (typeof value === 'undefined') {
        return msgid;
      } else {
        return (typeof value === 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      const value = django.catalog[singular];
      if (typeof value === 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      let value = django.gettext(context + '\x04' + msgid);
      if (value.includes('\x04')) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      let value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.includes('\x04')) {
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
      "%d-%m-%Y %H:%M:%S",
      "%d-%m-%y %H:%M:%S",
      "%Y-%m-%d %H:%M:%S",
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%y %H:%M:%S",
      "%Y/%m/%d %H:%M:%S",
      "%d-%m-%Y %H:%M:%S.%f",
      "%d-%m-%y %H:%M:%S.%f",
      "%Y-%m-%d %H:%M:%S.%f",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%y %H:%M:%S.%f",
      "%Y/%m/%d %H:%M:%S.%f",
      "%d-%m-%Y %H.%M:%S",
      "%d-%m-%y %H.%M:%S",
      "%d/%m/%Y %H.%M:%S",
      "%d/%m/%y %H.%M:%S",
      "%d-%m-%Y %H.%M:%S.%f",
      "%d-%m-%y %H.%M:%S.%f",
      "%d/%m/%Y %H.%M:%S.%f",
      "%d/%m/%y %H.%M:%S.%f",
      "%d-%m-%Y %H:%M",
      "%d-%m-%y %H:%M",
      "%Y-%m-%d %H:%M",
      "%d/%m/%Y %H:%M",
      "%d/%m/%y %H:%M",
      "%Y/%m/%d %H:%M",
      "%d-%m-%Y %H.%M",
      "%d-%m-%y %H.%M",
      "%d/%m/%Y %H.%M",
      "%d/%m/%y %H.%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j F Y",
    "DATE_INPUT_FORMATS": [
      "%d-%m-%Y",
      "%d-%m-%y",
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y/%m/%d",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "j-n-Y H:i",
    "SHORT_DATE_FORMAT": "j-n-Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "H:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H.%M:%S",
      "%H.%M:%S.%f",
      "%H.%M",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F Y"
  };

    django.get_format = function(format_type) {
      const value = django.formats[format_type];
      if (typeof value === 'undefined') {
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
};

