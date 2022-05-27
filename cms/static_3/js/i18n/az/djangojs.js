

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
      "%(sel)s / %(cnt)s se\u00e7ilib",
      "%(sel)s / %(cnt)s se\u00e7ilib"
    ],
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "April": "Aprel",
    "August": "Avqust",
    "Available %s": "M\u00fcmk\u00fcn %s",
    "Cancel": "L\u0259\u011fv et",
    "Choose": "Se\u00e7",
    "Choose a Date": "Tarix Se\u00e7in",
    "Choose a Time": "Vaxt Se\u00e7in",
    "Choose a time": "Vaxt\u0131 se\u00e7in",
    "Choose all": "Ham\u0131s\u0131n\u0131 se\u00e7",
    "Chosen %s": "Se\u00e7ilmi\u015f %s",
    "Click to choose all %s at once.": "B\u00fct\u00fcn %s siyah\u0131s\u0131n\u0131 se\u00e7m\u0259k \u00fc\u00e7\u00fcn t\u0131qlay\u0131n.",
    "Click to remove all chosen %s at once.": "Se\u00e7ilmi\u015f %s siyah\u0131s\u0131n\u0131n ham\u0131s\u0131n\u0131 silm\u0259k \u00fc\u00e7\u00fcn t\u0131qlay\u0131n.",
    "December": "Dekabr",
    "February": "Fevral",
    "Filter": "S\u00fczg\u0259c",
    "Hide": "Gizl\u0259t",
    "January": "Yanvar",
    "July": "\u0130yul",
    "June": "\u0130yun",
    "March": "Mart",
    "May": "May",
    "Midnight": "Gec\u0259 yar\u0131s\u0131",
    "Noon": "G\u00fcnorta",
    "Note: You are %s hour ahead of server time.": [
      "Diqq\u0259t: Server vaxt\u0131ndan %s saat ir\u0259lid\u0259siniz.",
      "Diqq\u0259t: Server vaxt\u0131ndan %s saat ir\u0259lid\u0259siniz."
    ],
    "Note: You are %s hour behind server time.": [
      "Diqq\u0259t: Server vaxt\u0131ndan %s saat gerid\u0259siniz.",
      "Diqq\u0259t: Server vaxt\u0131ndan %s saat gerid\u0259siniz."
    ],
    "November": "Noyabr",
    "Now": "\u0130ndi",
    "October": "Oktyabr",
    "Remove": "Y\u0131\u011f\u0131\u015fd\u0131r",
    "Remove all": "Ham\u0131s\u0131n\u0131 sil",
    "September": "Sentyabr",
    "Show": "G\u00f6st\u0259r",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Bu, m\u00fcmk\u00fcn %s siyah\u0131s\u0131d\u0131r. Onlardan bir ne\u00e7\u0259sini qar\u015f\u0131s\u0131ndak\u0131 xanaya i\u015far\u0259 qoymaq v\u0259 iki xana aras\u0131ndak\u0131 \"Se\u00e7\"i t\u0131qlamaqla se\u00e7m\u0259k olar.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Bu, se\u00e7ilmi\u015f %s siyah\u0131s\u0131d\u0131r. Onlardan bir ne\u00e7\u0259sini a\u015fa\u011f\u0131dak\u0131 xanaya i\u015far\u0259 qoymaq v\u0259 iki xana aras\u0131ndak\u0131 \"Sil\"i t\u0131qlamaqla silm\u0259k olar.",
    "Today": "Bu g\u00fcn",
    "Tomorrow": "Sabah",
    "Type into this box to filter down the list of available %s.": "Bu xanaya yazmaqla m\u00fcmk\u00fcn %s siyah\u0131s\u0131n\u0131 filtrl\u0259y\u0259 bil\u0259rsiniz.",
    "Yesterday": "D\u00fcn\u0259n",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "\u018fm\u0259liyyat se\u00e7misiniz v\u0259 f\u0259rdi sah\u0259l\u0259rd\u0259 d\u0259yi\u015fikl\u0259r etm\u0259misiniz. B\u00f6y\u00fck ehtimal Saxla d\u00fcym\u0259si yerin\u0259 Get d\u00fcym\u0259sin\u0259 ehtiyyac\u0131n\u0131z var.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "\u018fm\u0259liyyat se\u00e7misiniz, amma f\u0259rdi sah\u0259l\u0259rd\u0259ki d\u0259yi\u015fiklikl\u0259riniz h\u0259l\u0259 d\u0259 yadda saxlan\u0131lmay\u0131b. Saxlamaq \u00fc\u00e7\u00fcn l\u00fctf\u0259n Tamam d\u00fcym\u0259sin\u0259 klikl\u0259yin. \u018fm\u0259liyyat\u0131 t\u0259krar i\u015fl\u0259tm\u0259li olacaqs\u0131n\u0131z.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "B\u0259zi sah\u0259l\u0259rd\u0259 etdiyiniz d\u0259yi\u015fiklikl\u0259ri h\u0259l\u0259 yadda saxlamam\u0131\u015f\u0131q. \u018fg\u0259r \u0259m\u0259liyyat\u0131 i\u015f\u0259 salsan\u0131z, d\u0259yi\u015fiklikl\u0259r \u0259ld\u0259n ged\u0259c\u0259k.",
    "one letter Friday\u0004F": "C",
    "one letter Monday\u0004M": "B",
    "one letter Saturday\u0004S": "\u015e",
    "one letter Sunday\u0004S": "B",
    "one letter Thursday\u0004T": "C",
    "one letter Tuesday\u0004T": "\u00c7",
    "one letter Wednesday\u0004W": "\u00c7"
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
    "DATETIME_FORMAT": "j E Y, G:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H:%M",
      "%d.%m.%y %H:%M:%S",
      "%d.%m.%y %H:%M:%S.%f",
      "%d.%m.%y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j E Y",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y",
      "%d.%m.%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
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

