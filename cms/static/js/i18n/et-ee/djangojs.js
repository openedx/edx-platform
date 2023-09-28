

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
      "%(sel)s  %(cnt)sst valitud",
      "%(sel)s  %(cnt)sst valitud"
    ],
    "6 a.m.": "6 hommikul",
    "6 p.m.": "6 \u00f5htul",
    "April": "aprill",
    "August": "august",
    "Available %s": "Saadaval %s",
    "Cancel": "T\u00fchista",
    "Choose": "Vali",
    "Choose a Date": "Vali kuup\u00e4ev",
    "Choose a Time": "Vali aeg",
    "Choose a time": "Vali aeg",
    "Choose all": "Vali k\u00f5ik",
    "Chosen %s": "Valitud %s",
    "Click to choose all %s at once.": "Kliki, et valida k\u00f5ik %s korraga.",
    "Click to remove all chosen %s at once.": "Kliki, et eemaldada k\u00f5ik valitud %s korraga.",
    "December": "detsember",
    "February": "veebruar",
    "Filter": "Filter",
    "Hide": "Varja",
    "January": "jaanuar",
    "July": "juuli",
    "June": "juuni",
    "March": "m\u00e4rts",
    "May": "mai",
    "Midnight": "Kesk\u00f6\u00f6",
    "Noon": "Keskp\u00e4ev",
    "Note: You are %s hour ahead of server time.": [
      "M\u00e4rkus: Olete %s tund serveri ajast ees.",
      "M\u00e4rkus: Olete %s tundi serveri ajast ees."
    ],
    "Note: You are %s hour behind server time.": [
      "M\u00e4rkus: Olete %s tund serveri ajast maas.",
      "M\u00e4rkus: Olete %s tundi serveri ajast maas."
    ],
    "November": "november",
    "Now": "Praegu",
    "October": "oktoober",
    "Remove": "Eemalda",
    "Remove all": "Eemalda k\u00f5ik",
    "September": "september",
    "Show": "N\u00e4ita",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Nimekiri v\u00e4lja \"%s\" v\u00f5imalikest v\u00e4\u00e4rtustest. Saad valida \u00fche v\u00f5i mitu kirjet allolevast kastist ning vajutades noolt \"Vali\" liigutada neid \u00fchest kastist teise.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Nimekiri v\u00e4lja \"%s\" valitud v\u00e4\u00e4rtustest. Saad valida \u00fche v\u00f5i mitu kirjet allolevast kastist ning vajutades noolt \"Eemalda\" liigutada neid \u00fchest kastist teise.",
    "Today": "T\u00e4na",
    "Tomorrow": "Homme",
    "Type into this box to filter down the list of available %s.": "Filtreeri selle kasti abil v\u00e4lja \"%s\" nimekirja.",
    "Yesterday": "Eile",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Valisite toimingu, kuid ei muutnud \u00fchtegi lahtrit. T\u00f5en\u00e4oliselt otsite Mine mitte Salvesta nuppu.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Valisite toimingu, kuid pole salvestanud muudatusi lahtrites. Salvestamiseks palun vajutage OK. Peate toimingu uuesti k\u00e4ivitama.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Muudetavates lahtrites on salvestamata muudatusi. Kui sooritate m\u00f5ne toimingu, l\u00e4hevad salvestamata muudatused kaotsi.",
    "abbrev. month April\u0004Apr": "apr",
    "abbrev. month August\u0004Aug": "aug",
    "abbrev. month December\u0004Dec": "dets",
    "abbrev. month February\u0004Feb": "veebr",
    "abbrev. month January\u0004Jan": "jaan",
    "abbrev. month July\u0004Jul": "juuli",
    "abbrev. month June\u0004Jun": "juuni",
    "abbrev. month March\u0004Mar": "m\u00e4rts",
    "abbrev. month May\u0004May": "mai",
    "abbrev. month November\u0004Nov": "nov",
    "abbrev. month October\u0004Oct": "okt",
    "abbrev. month September\u0004Sep": "sept",
    "one letter Friday\u0004F": "R",
    "one letter Monday\u0004M": "E",
    "one letter Saturday\u0004S": "L",
    "one letter Sunday\u0004S": "P",
    "one letter Thursday\u0004T": "N",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "K"
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
    "DATETIME_FORMAT": "N j, Y, P",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%m/%d/%Y %H:%M:%S",
      "%m/%d/%Y %H:%M:%S.%f",
      "%m/%d/%Y %H:%M",
      "%m/%d/%y %H:%M:%S",
      "%m/%d/%y %H:%M:%S.%f",
      "%m/%d/%y %H:%M"
    ],
    "DATE_FORMAT": "j. F Y",
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
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "G:i",
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

