

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
      "U p\u00ebrzgjodh %(sel)s nga %(cnt)s",
      "U p\u00ebrzgjodh\u00ebn %(sel)s nga %(cnt)s"
    ],
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "April": "Prill",
    "August": "Gusht",
    "Available %s": "%s i gatsh\u00ebm",
    "Cancel": "Anuloje",
    "Choose": "Zgjidhni",
    "Choose a Date": "Zgjidhni nj\u00eb Dat\u00eb",
    "Choose a Time": "Zgjidhni nj\u00eb Koh\u00eb",
    "Choose a time": "Zgjidhni nj\u00eb koh\u00eb",
    "Choose all": "Zgjidheni krejt",
    "Chosen %s": "U zgjodh %s",
    "Click to choose all %s at once.": "Klikoni q\u00eb t\u00eb zgjidhen krejt %s nj\u00ebher\u00ebsh.",
    "Click to remove all chosen %s at once.": "Klikoni q\u00eb t\u00eb hiqen krejt %s e zgjedhura nj\u00ebher\u00ebsh.",
    "December": "Dhjetor",
    "Error": "Problem",
    "February": "Shkurt",
    "Filter": "Filtro",
    "Hide": "Fshihe",
    "January": "Janar",
    "July": "Korrik",
    "June": "Qershor",
    "March": "Mars",
    "May": "Maj",
    "Midnight": "Mesnat\u00eb",
    "Noon": "Mesdit\u00eb",
    "Not Selected": "E pa selektuar",
    "Note: You are %s hour ahead of server time.": [
      "Sh\u00ebnim: Jeni %s or\u00eb para koh\u00ebs s\u00eb sh\u00ebrbyesit.",
      "Sh\u00ebnim: Jeni %s or\u00eb para koh\u00ebs s\u00eb sh\u00ebrbyesit."
    ],
    "Note: You are %s hour behind server time.": [
      "Sh\u00ebnim: Jeni %s or\u00eb pas koh\u00ebs s\u00eb sh\u00ebrbyesit.",
      "Sh\u00ebnim: Jeni %s or\u00eb pas koh\u00ebs s\u00eb sh\u00ebrbyesit."
    ],
    "November": "N\u00ebntor",
    "Now": "Tani",
    "October": "Tetor",
    "Option Deleted": "Opsioni u fshia",
    "Remove": "Hiqe",
    "Remove all": "Hiqi krejt",
    "Saving...": "Ruaj...",
    "September": "Shtator",
    "Show": "Shfaqe",
    "Status of Your Response": "Statusi i p\u00ebrgjigjjes suaj",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Kjo \u00ebsht\u00eb lista e %s t\u00eb gatsh\u00ebm. Mund t\u00eb zgjidhni disa duke i p\u00ebrzgjedhur te kutiza m\u00eb posht\u00eb dhe mandej duke klikuar mbi shigjet\u00ebn \"Zgjidhe\" mes dy kutizave.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Kjo \u00ebsht\u00eb lista e %s t\u00eb gatshme. Mund t\u00eb hiqni disa duke i p\u00ebrzgjedhur te kutiza m\u00eb posht\u00eb e mandej duke klikuar mbi shigjet\u00ebn \"Hiqe\" mes dy kutizave.",
    "This response could not be saved.": "P\u00ebrgjigjja nuk mund t\u00eb ruhet.",
    "This response has been saved but not submitted.": "Kjo p\u00ebrgjigjje \u00ebsht\u00eb ruajtur por nuk \u00ebsht\u00eb paraqitur.",
    "This response has not been saved.": "Kjo p\u00ebrgjigjje nuk \u00ebsht\u00eb ruajtur.",
    "Today": "Sot",
    "Tomorrow": "Nes\u00ebr",
    "Type into this box to filter down the list of available %s.": "Shkruani brenda kutiz\u00ebs q\u00eb t\u00eb filtrohet lista e %s t\u00eb passhme.",
    "Unnamed Option": "Opsion i pa em\u00ebrtuar",
    "Warning": "Paralajm\u00ebrim",
    "Yesterday": "Dje",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Keni p\u00ebrzgjedhur nj\u00eb veprim, dhe nuk keni b\u00ebr\u00eb ndonj\u00eb ndryshim te fusha individuale. Ndoshta po k\u00ebrkonit p\u00ebr butonin Shko, n\u00eb vend se p\u00ebr butonin Ruaje.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Keni p\u00ebrzgjedhur nj\u00eb veprim, por s\u2019keni ruajtur ende ndryshimet q\u00eb b\u00ebt\u00eb te fusha individuale. Ju lutemi, klikoni OK q\u00eb t\u00eb b\u00ebhet ruajtja. Do t\u2019ju duhet ta rib\u00ebni veprimin.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Keni ndryshime t\u00eb paruajtura te fusha individuale t\u00eb ndryshueshme. N\u00ebse kryeni nj\u00eb veprim, ndryshimet e paruajtura do t\u00eb humbin.",
    "abbrev. month April\u0004Apr": "Pri",
    "abbrev. month August\u0004Aug": "Gus",
    "abbrev. month December\u0004Dec": "Dhje",
    "abbrev. month February\u0004Feb": "Shk",
    "abbrev. month January\u0004Jan": "Jan",
    "abbrev. month July\u0004Jul": "Kor",
    "abbrev. month June\u0004Jun": "Qer",
    "abbrev. month March\u0004Mar": "Mar",
    "abbrev. month May\u0004May": "Maj",
    "abbrev. month November\u0004Nov": "N\u00ebn",
    "abbrev. month October\u0004Oct": "Tet",
    "abbrev. month September\u0004Sep": "Sht",
    "one letter Friday\u0004F": "P",
    "one letter Monday\u0004M": "H",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "E",
    "one letter Tuesday\u0004T": "M",
    "one letter Wednesday\u0004W": "M"
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
    "DATE_FORMAT": "d F Y",
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
    "MONTH_DAY_FORMAT": "j F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "Y-m-d",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "g.i.A",
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

