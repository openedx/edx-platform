

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2;
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
      "odabrano %(sel)s od %(cnt)s",
      "odabrano %(sel)s od %(cnt)s",
      "odabrano %(sel)s od %(cnt)s"
    ],
    "6 a.m.": "6 ujutro",
    "6 p.m.": "6 popodne",
    "Available %s": "Dostupno %s",
    "Cancel": "Odustani",
    "Choose": "Izaberi",
    "Choose a Date": "Odaberite datum",
    "Choose a Time": "Izaberite vrijeme",
    "Choose a time": "Izaberite vrijeme",
    "Choose all": "Odaberi sve",
    "Chosen %s": "Odabrano %s",
    "Click to choose all %s at once.": "Kliknite da odabrete sve %s odjednom.",
    "Click to remove all chosen %s at once.": "Kliknite da uklonite sve izabrane %s odjednom.",
    "Filter": "Filter",
    "Hide": "Sakri",
    "Midnight": "Pono\u0107",
    "Noon": "Podne",
    "Now": "Sada",
    "Remove": "Ukloni",
    "Remove all": "Ukloni sve",
    "Show": "Prika\u017ei",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Ovo je popis dostupnih %s. Mo\u017eete dodati pojedine na na\u010din da ih izaberete u polju ispod i kliknete \"Izaberi\" strelicu izme\u0111u dva polja. ",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Ovo je popis odabranih %s. Mo\u017eete ukloniti pojedine na na\u010din da ih izaberete u polju ispod i kliknete \"Ukloni\" strelicu izme\u0111u dva polja. ",
    "Today": "Danas",
    "Tomorrow": "Sutra",
    "Type into this box to filter down the list of available %s.": "Tipkajte u ovo polje da filtrirate listu dostupnih %s.",
    "Yesterday": "Ju\u010der",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Odabrali ste akciju, a niste napravili nikakve izmjene na pojedinim poljima. Vjerojatno tra\u017eite gumb Idi umjesto gumb Spremi.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Odabrali ste akciju, ali niste jo\u0161 spremili promjene na pojedinim polja. Molimo kliknite OK za spremanje. Morat \u0107ete ponovno pokrenuti akciju.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Neke promjene nisu spremljene na pojedinim polja za ure\u0111ivanje. Ako pokrenete akciju, nespremljene promjene \u0107e biti izgubljene."
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
    "DATETIME_FORMAT": "j. E Y. H:i",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d",
      "%d.%m.%Y. %H:%M:%S",
      "%d.%m.%Y. %H:%M:%S.%f",
      "%d.%m.%Y. %H:%M",
      "%d.%m.%Y.",
      "%d.%m.%y. %H:%M:%S",
      "%d.%m.%y. %H:%M:%S.%f",
      "%d.%m.%y. %H:%M",
      "%d.%m.%y.",
      "%d. %m. %Y. %H:%M:%S",
      "%d. %m. %Y. %H:%M:%S.%f",
      "%d. %m. %Y. %H:%M",
      "%d. %m. %Y.",
      "%d. %m. %y. %H:%M:%S",
      "%d. %m. %y. %H:%M:%S.%f",
      "%d. %m. %y. %H:%M",
      "%d. %m. %y."
    ],
    "DATE_FORMAT": "j. E Y.",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%d.%m.%Y.",
      "%d.%m.%y.",
      "%d. %m. %Y.",
      "%d. %m. %y."
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "j.m.Y. H:i",
    "SHORT_DATE_FORMAT": "j.m.Y.",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "H:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F Y."
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

