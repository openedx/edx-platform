

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = 0;
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
      "%(sel)s daripada %(cnt)s dipilih"
    ],
    "6 a.m.": "6 pagi",
    "6 p.m.": "6 malam",
    "April": "Arpil",
    "August": "Ogos",
    "Available %s": "%s tersedia",
    "Cancel": "Batal",
    "Choose": "Pilih",
    "Choose a Date": "Pilih Tarikh",
    "Choose a Time": "Pilih Masa",
    "Choose a time": "Pilih masa",
    "Choose all": "Pilih semua",
    "Chosen %s": "%s dipilh",
    "Click to choose all %s at once.": "Klik untuk memlih semua %s serentak.",
    "Click to remove all chosen %s at once.": "Klik untuk membuang serentak semua %s yang dipilih.",
    "December": "Disember",
    "February": "Februari",
    "Filter": "Tapis",
    "Hide": "Sorok",
    "January": "Januari",
    "July": "Julai",
    "June": "Jun",
    "March": "Mac",
    "May": "Mei",
    "Midnight": "Tengah malam",
    "Noon": "Tengahari",
    "Note: You are %s hour ahead of server time.": [
      "Nota: Anda %s jam ke depan daripada masa pelayan."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: Anda %s jam ke belakang daripada masa pelayan."
    ],
    "November": "November",
    "Now": "Sekarang",
    "October": "Oktober",
    "Remove": "Buang",
    "Remove all": "Buang semua",
    "September": "September",
    "Show": "Tunjuk",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Ini adalah senarai %s yang tersedia. Anda boleh memilih beberapa dengan memilihnya di dalam kotak dibawah dan kemudian klik pada anak panah \"Pilih\" diantara dua kotak itu.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Ini adalah senarai %s yang dipilih. Anda boleh membuangnya dengan memilihnya pada kotak dibawah dan kemudian klik pada anak panah \"Buang\" diantara dua kotak itu.",
    "Today": "Hari ini",
    "Tomorrow": "Esok",
    "Type into this box to filter down the list of available %s.": "Taip didalam kotak untuk menapis senarai %s yang tersedia.",
    "Yesterday": "Semalam",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Anda telah memilih sesuatu tindakan, dan belum membuat perubahan pada medan-medan individu. Anda mungkin sedang mencari butang Pergi dan bukannya butang Simpan.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Anda telah memlih tindakan, tetapi anda belum menyimpan perubahan yang dilakukan pada medan-medan individu. Sila klik OK to untuk simpan. Anda perlu melakukan semula tindakan tersebut.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Anda mempunyai perubahan yang belum disimpan pada medan-medan individu yang boleh di-edit. Sekiranya anda melakukan sebarang tindakan, penukaran yang tidak disimpan akan hilang.",
    "abbrev. month April\u0004Apr": "Apr",
    "abbrev. month August\u0004Aug": "Ogo",
    "abbrev. month December\u0004Dec": "Dis",
    "abbrev. month February\u0004Feb": "Feb",
    "abbrev. month January\u0004Jan": "Jan",
    "abbrev. month July\u0004Jul": "Jul",
    "abbrev. month June\u0004Jun": "Jun",
    "abbrev. month March\u0004Mar": "Mar",
    "abbrev. month May\u0004May": "Mei",
    "abbrev. month November\u0004Nov": "Nov",
    "abbrev. month October\u0004Oct": "Okt",
    "abbrev. month September\u0004Sep": "Sep",
    "one letter Friday\u0004F": "J",
    "one letter Monday\u0004M": "I",
    "one letter Saturday\u0004S": "Sa",
    "one letter Sunday\u0004S": "A",
    "one letter Thursday\u0004T": "K",
    "one letter Tuesday\u0004T": "Se",
    "one letter Wednesday\u0004W": "R"
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
    "DATETIME_FORMAT": "j M Y, P",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j M Y",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%d/%m/%Y",
      "%d/%m/%y",
      "%d %b %Y",
      "%d %b, %Y",
      "%d %B %Y",
      "%d %B, %Y"
    ],
    "DECIMAL_SEPARATOR": ".",
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d/m/Y P",
    "SHORT_DATE_FORMAT": "d/m/Y",
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

