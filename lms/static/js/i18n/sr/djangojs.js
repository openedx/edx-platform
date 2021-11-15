

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);
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
      "%(sel)s \u043e\u0434 %(cnt)s \u0438\u0437\u0430\u0431\u0440\u0430\u043d",
      "%(sel)s \u043e\u0434 %(cnt)s \u0438\u0437\u0430\u0431\u0440\u0430\u043d\u0430",
      "%(sel)s \u043e\u0434 %(cnt)s \u0438\u0437\u0430\u0431\u0440\u0430\u043d\u0438\u0445"
    ],
    "6 a.m.": "18\u0447",
    "6 p.m.": "18\u0447",
    "April": "\u0410\u043f\u0440\u0438\u043b",
    "August": "\u0410\u0432\u0433\u0443\u0441\u0442",
    "Available %s": "\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u0438 %s",
    "Cancel": "\u041f\u043e\u043d\u0438\u0448\u0442\u0438",
    "Choose": "\u0418\u0437\u0430\u0431\u0435\u0440\u0438",
    "Choose a Date": "\u041e\u0434\u0430\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0430\u0442\u0443\u043c",
    "Choose a Time": "\u041e\u0434\u0430\u0431\u0435\u0440\u0438\u0442\u0435 \u0432\u0440\u0435\u043c\u0435",
    "Choose a time": "\u041e\u0434\u0430\u0431\u0438\u0440 \u0432\u0440\u0435\u043c\u0435\u043d\u0430",
    "Choose all": "\u0418\u0437\u0430\u0431\u0435\u0440\u0438 \u0441\u0432\u0435",
    "Chosen %s": "\u0418\u0437\u0430\u0431\u0440\u0430\u043d\u043e \u201e%s\u201c",
    "Click to choose all %s at once.": "\u0418\u0437\u0430\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0432\u0435 \u201e%s\u201c \u043e\u0434\u0458\u0435\u0434\u043d\u043e\u043c.",
    "Click to remove all chosen %s at once.": "\u0423\u043a\u043b\u043e\u043d\u0438\u0442\u0435 \u0441\u0432\u0435 \u0438\u0437\u0430\u0431\u0440\u0430\u043d\u0435 \u201e%s\u201c \u043e\u0434\u0458\u0435\u0434\u043d\u043e\u043c.",
    "December": "\u0414\u0435\u0446\u0435\u043c\u0431\u0430\u0440",
    "February": "\u0424\u0435\u0431\u0440\u0443\u0430\u0440",
    "Filter": "\u0424\u0438\u043b\u0442\u0435\u0440",
    "Hide": "\u0421\u0430\u043a\u0440\u0438\u0458",
    "January": "\u0408\u0430\u043d\u0443\u0430\u0440",
    "July": "\u0408\u0443\u043b",
    "June": "\u0408\u0443\u043d",
    "March": "\u041c\u0430\u0440\u0442",
    "May": "\u041c\u0430\u0458",
    "Midnight": "\u041f\u043e\u043d\u043e\u045b",
    "Noon": "\u041f\u043e\u0434\u043d\u0435",
    "Note: You are %s hour ahead of server time.": [
      "\u041e\u0431\u0430\u0432\u0435\u0448\u0442\u0435\u045a\u0435: %s \u0441\u0430\u0442 \u0441\u0442\u0435 \u0438\u0441\u043f\u0440\u0435\u0434 \u0441\u0435\u0440\u0432\u0435\u0440\u0441\u043a\u043e\u0433 \u0432\u0440\u0435\u043c\u0435\u043d\u0430.",
      "\u041e\u0431\u0430\u0432\u0435\u0448\u0442\u0435\u045a\u0435: %s \u0441\u0430\u0442\u0430 \u0441\u0442\u0435 \u0438\u0441\u043f\u0440\u0435\u0434 \u0441\u0435\u0440\u0432\u0435\u0440\u0441\u043a\u043e\u0433 \u0432\u0440\u0435\u043c\u0435\u043d\u0430.",
      "\u041e\u0431\u0430\u0432\u0435\u0448\u0442\u0435\u045a\u0435: %s \u0441\u0430\u0442\u0438 \u0441\u0442\u0435 \u0438\u0441\u043f\u0440\u0435\u0434 \u0441\u0435\u0440\u0432\u0435\u0440\u0441\u043a\u043e\u0433 \u0432\u0440\u0435\u043c\u0435\u043d\u0430."
    ],
    "Note: You are %s hour behind server time.": [
      "\u041e\u0431\u0430\u0432\u0435\u0448\u0442\u0435\u045a\u0435: %s \u0441\u0430\u0442 \u0441\u0442\u0435 \u0438\u0437\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0441\u043a\u043e\u0433 \u0432\u0440\u0435\u043c\u0435\u043d\u0430.",
      "\u041e\u0431\u0430\u0432\u0435\u0448\u0442\u0435\u045a\u0435: %s \u0441\u0430\u0442\u0430 \u0441\u0442\u0435 \u0438\u0437\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0441\u043a\u043e\u0433 \u0432\u0440\u0435\u043c\u0435\u043d\u0430.",
      "\u041e\u0431\u0430\u0432\u0435\u0448\u0442\u0435\u045a\u0435: %s \u0441\u0430\u0442\u0438 \u0441\u0442\u0435 \u0438\u0437\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0441\u043a\u043e\u0433 \u0432\u0440\u0435\u043c\u0435\u043d\u0430."
    ],
    "November": "\u041d\u043e\u0432\u0435\u043c\u0431\u0430\u0440",
    "Now": "\u0422\u0440\u0435\u043d\u0443\u0442\u043d\u043e \u0432\u0440\u0435\u043c\u0435",
    "October": "\u041e\u043a\u0442\u043e\u0431\u0430\u0440",
    "Remove": "\u0423\u043a\u043b\u043e\u043d\u0438",
    "Remove all": "\u0423\u043a\u043b\u043e\u043d\u0438 \u0441\u0432\u0435",
    "September": "\u0421\u0435\u043f\u0442\u0435\u043c\u0431\u0430\u0440",
    "Show": "\u041f\u043e\u043a\u0430\u0436\u0438",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u041e\u0432\u043e \u0458\u0435 \u043b\u0438\u0441\u0442\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0438\u0445 \u201e%s\u201c. \u041c\u043e\u0436\u0435\u0442\u0435 \u0438\u0437\u0430\u0431\u0440\u0430\u0442\u0438 \u0435\u043b\u0435\u043c\u0435\u043d\u0442\u0435 \u0442\u0430\u043a\u043e \u0448\u0442\u043e \u045b\u0435\u0442\u0435 \u0438\u0445 \u0438\u0437\u0430\u0431\u0440\u0430\u0442\u0438 \u0443 \u043b\u0438\u0441\u0442\u0438 \u0438 \u043a\u043b\u0438\u043a\u043d\u0443\u0442\u0438 \u043d\u0430 \u201e\u0418\u0437\u0430\u0431\u0435\u0440\u0438\u201c.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u041e\u0432\u043e \u0458\u0435 \u043b\u0438\u0441\u0442\u0430 \u0438\u0437\u0430\u0431\u0440\u0430\u043d\u0438\u0445 \u201e%s\u201c. \u041c\u043e\u0436\u0435\u0442\u0435 \u0443\u043a\u043b\u043e\u043d\u0438\u0442\u0438 \u0435\u043b\u0435\u043c\u0435\u043d\u0442\u0435 \u0442\u0430\u043a\u043e \u0448\u0442\u043e \u045b\u0435\u0442\u0435 \u0438\u0445 \u0438\u0437\u0430\u0431\u0440\u0430\u0442\u0438 \u0443 \u043b\u0438\u0441\u0442\u0438 \u0438 \u043a\u043b\u0438\u043a\u043d\u0443\u0442\u0438 \u043d\u0430 \u201e\u0423\u043a\u043b\u043e\u043d\u0438\u201c.",
    "Today": "\u0414\u0430\u043d\u0430\u0441",
    "Tomorrow": "\u0421\u0443\u0442\u0440\u0430",
    "Type into this box to filter down the list of available %s.": "\u0424\u0438\u043b\u0442\u0440\u0438\u0440\u0430\u0458\u0442\u0435 \u043b\u0438\u0441\u0442\u0443 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0438\u0445 \u0435\u043b\u0435\u043c\u0435\u043d\u0430\u0442\u0430 \u201e%s\u201c.",
    "Yesterday": "\u0408\u0443\u0447\u0435",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "\u0418\u0437\u0430\u0431\u0440\u0430\u043b\u0438 \u0441\u0442\u0435 \u0430\u043a\u0446\u0438\u0458\u0443 \u0438 \u043d\u0438\u0441\u0442\u0435 \u043d\u0430\u043f\u0440\u0430\u0432\u0438\u043b\u0438 \u043d\u0438\u0458\u0435\u0434\u043d\u0443 \u043f\u0440\u043e\u043c\u0435\u043d\u0443 \u043d\u0430 \u043f\u043e\u0458\u0435\u0434\u0438\u043d\u0430\u0447\u043d\u0438\u043c \u043f\u043e\u0459\u0438\u043c\u0430. \u0412\u0435\u0440\u043e\u0432\u0430\u0442\u043d\u043e \u0442\u0440\u0430\u0436\u0438\u0442\u0435 \u041a\u0440\u0435\u043d\u0438 \u0434\u0443\u0433\u043c\u0435 \u0443\u043c\u0435\u0441\u0442\u043e \u0421\u0430\u0447\u0443\u0432\u0430\u0458.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "\u0418\u0437\u0430\u0431\u0440\u0430\u043b\u0438 \u0441\u0442\u0435 \u0430\u043a\u0446\u0438\u0458\u0443, \u0430\u043b\u0438 \u043d\u0438\u0441\u0442\u0435 \u0441\u0430\u0447\u0443\u0432\u0430\u043b\u0438 \u0432\u0430\u0448\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u0435 \u0443 \u043f\u043e\u0458\u0435\u0434\u0438\u043d\u0430\u0447\u043d\u0430 \u043f\u043e\u0459\u0430. \u041a\u043b\u0438\u043a\u043d\u0438\u0442\u0435 \u043d\u0430 OK \u0434\u0430 \u0441\u0430\u0447\u0443\u0432\u0430\u0442\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u0435. \u0411\u0438\u045b\u0435 \u043d\u0435\u043e\u043f\u0445\u043e\u0434\u043d\u043e \u0434\u0430 \u043f\u043e\u043d\u043e\u0432\u043e \u043f\u043e\u043a\u0440\u0435\u043d\u0435\u0442\u0435 \u0430\u043a\u0446\u0438\u0458\u0443.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0418\u043c\u0430\u0442\u0435 \u043d\u0435\u0441\u0430\u0447\u0438\u0432\u0430\u043d\u0435 \u0438\u0437\u043c\u0435\u043d\u0435. \u0410\u043a\u043e \u043f\u043e\u043a\u0440\u0435\u043d\u0435\u0442\u0435 \u0430\u043a\u0446\u0438\u0458\u0443, \u0438\u0437\u043c\u0435\u043d\u0435 \u045b\u0435 \u0431\u0438\u0442\u0438 \u0438\u0437\u0433\u0443\u0431\u0459\u0435\u043d\u0435.",
    "abbrev. month April\u0004Apr": "\u0430\u043f\u0440",
    "abbrev. month August\u0004Aug": "\u0430\u0432\u0433",
    "abbrev. month December\u0004Dec": "\u0434\u0435\u0446",
    "abbrev. month February\u0004Feb": "\u0444\u0435\u0431",
    "abbrev. month January\u0004Jan": "\u0458\u0430\u043d",
    "abbrev. month July\u0004Jul": "\u0458\u0443\u043b",
    "abbrev. month June\u0004Jun": "\u0458\u0443\u043d",
    "abbrev. month March\u0004Mar": "\u043c\u0430\u0440\u0442",
    "abbrev. month May\u0004May": "\u043c\u0430\u0458",
    "abbrev. month November\u0004Nov": "\u043d\u043e\u0432",
    "abbrev. month October\u0004Oct": "\u043e\u043a\u0442",
    "abbrev. month September\u0004Sep": "\u0441\u0435\u043f",
    "one letter Friday\u0004F": "\u041f",
    "one letter Monday\u0004M": "\u041f",
    "one letter Saturday\u0004S": "\u0421",
    "one letter Sunday\u0004S": "\u041d",
    "one letter Thursday\u0004T": "\u0427",
    "one letter Tuesday\u0004T": "\u0423",
    "one letter Wednesday\u0004W": "\u0421"
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
    "DATETIME_FORMAT": "j. F Y. H:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y. %H:%M:%S",
      "%d.%m.%Y. %H:%M:%S.%f",
      "%d.%m.%Y. %H:%M",
      "%d.%m.%y. %H:%M:%S",
      "%d.%m.%y. %H:%M:%S.%f",
      "%d.%m.%y. %H:%M",
      "%d. %m. %Y. %H:%M:%S",
      "%d. %m. %Y. %H:%M:%S.%f",
      "%d. %m. %Y. %H:%M",
      "%d. %m. %y. %H:%M:%S",
      "%d. %m. %y. %H:%M:%S.%f",
      "%d. %m. %y. %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j. F Y.",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y.",
      "%d.%m.%y.",
      "%d. %m. %Y.",
      "%d. %m. %y.",
      "%Y-%m-%d"
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

