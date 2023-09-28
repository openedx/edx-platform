

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
      "%(sel)s \u043d\u0430 %(cnt)s \u0435 \u0438\u0437\u0431\u0440\u0430\u043d",
      "%(sel)s \u043d\u0430 %(cnt)s \u0441\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438"
    ],
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 \u0441\u043b\u0435\u0434 \u043e\u0431\u044f\u0434",
    "April": "\u0410\u043f\u0440\u0438\u043b",
    "August": "\u0410\u0432\u0433\u0443\u0441\u0442",
    "Available %s": "\u041d\u0430\u043b\u0438\u0447\u043d\u0438 %s",
    "Cancel": "\u041e\u0442\u043a\u0430\u0437",
    "Choose": "\u0418\u0437\u0431\u0438\u0440\u0430\u043c",
    "Choose a Date": "\u0418\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u0430\u0442\u0430",
    "Choose a Time": "\u0418\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0432\u0440\u0435\u043c\u0435",
    "Choose a time": "\u0418\u0437\u0431\u0435\u0440\u0438 \u0432\u0440\u0435\u043c\u0435",
    "Choose all": "\u0418\u0437\u0431\u0435\u0440\u0438 \u0432\u0441\u0438\u0447\u043a\u0438",
    "Chosen %s": "\u0418\u0437\u0431\u0440\u0430\u0445\u043c\u0435 %s",
    "Click to choose all %s at once.": "\u041a\u043b\u0438\u043a\u043d\u0435\u0442\u0435, \u0437\u0430 \u0434\u0430 \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0432\u0441\u0438\u0447\u043a\u0438 %s \u043d\u0430\u0432\u0435\u0434\u043d\u044a\u0436.",
    "Click to remove all chosen %s at once.": "\u041a\u043b\u0438\u043a\u043d\u0435\u0442\u0435, \u0437\u0430 \u0434\u0430 \u043f\u0440\u0435\u043c\u0430\u0445\u043d\u0435\u0442\u0435 \u0432\u0441\u0438\u0447\u043a\u0438 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 %s \u043d\u0430\u0432\u0435\u0434\u043d\u044a\u0436.",
    "December": "\u0414\u0435\u043a\u0435\u043c\u0432\u0440\u0438",
    "February": "\u0424\u0435\u0432\u0440\u0443\u0430\u0440\u0438",
    "Filter": "\u0424\u0438\u043b\u0442\u044a\u0440",
    "Hide": "\u0421\u043a\u0440\u0438\u0439",
    "January": "\u042f\u043d\u0443\u0430\u0440\u0438",
    "July": "\u042e\u043b\u0438",
    "June": "\u042e\u043d\u0438",
    "March": "\u041c\u0430\u0440\u0442",
    "May": "\u041c\u0430\u0439",
    "Midnight": "\u041f\u043e\u043b\u0443\u043d\u043e\u0449",
    "Noon": "\u041f\u043e \u043e\u0431\u044f\u0434",
    "Note: You are %s hour ahead of server time.": [
      "\u0411\u0435\u043b\u0435\u0436\u043a\u0430: \u0412\u0438\u0435 \u0441\u0442\u0435 %s \u0447\u0430\u0441 \u043d\u0430\u043f\u0440\u0435\u0434 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u0442\u043e \u043d\u0430 \u0441\u044a\u0440\u0432\u044a\u0440\u0430.",
      "\u0411\u0435\u043b\u0435\u0436\u043a\u0430: \u0412\u0438\u0435 \u0441\u0442\u0435 %s \u0447\u0430\u0441\u0430 \u043d\u0430\u043f\u0440\u0435\u0434 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u0442\u043e \u043d\u0430 \u0441\u044a\u0440\u0432\u044a\u0440\u0430"
    ],
    "Note: You are %s hour behind server time.": [
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0438\u0435 \u0441\u0442\u0435 %s \u0447\u0430\u0441 \u043d\u0430\u0437\u0430\u0434 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u0442\u043e \u043d\u0430 \u0441\u044a\u0440\u0432\u044a\u0440\u0430.",
      "\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435: \u0412\u0438\u0435 \u0441\u0442\u0435 %s \u0447\u0430\u0441\u0430 \u043d\u0430\u0437\u0430\u0434 \u043e\u0442 \u0432\u0440\u0435\u043c\u0435\u0442\u043e \u043d\u0430 \u0441\u044a\u0440\u0432\u044a\u0440\u0430."
    ],
    "November": "\u041d\u043e\u0435\u043c\u0432\u0440\u0438",
    "Now": "\u0421\u0435\u0433\u0430",
    "October": "\u041e\u043a\u0442\u043e\u043c\u0432\u0440\u0438",
    "Remove": "\u041f\u0440\u0435\u043c\u0430\u0445\u043d\u0438",
    "Remove all": "\u041f\u0440\u0435\u043c\u0430\u0445\u0432\u0430\u043d\u0435 \u043d\u0430 \u0432\u0441\u0438\u0447\u043a\u0438",
    "September": "\u0421\u0435\u043f\u0442\u0435\u043c\u0432\u0440\u0438",
    "Show": "\u041f\u043e\u043a\u0430\u0436\u0438",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u0422\u043e\u0432\u0430 \u0435 \u0441\u043f\u0438\u0441\u044a\u043a \u043d\u0430 \u043d\u0430\u043b\u0438\u0447\u043d\u0438\u0442\u0435 %s . \u041c\u043e\u0436\u0435\u0442\u0435 \u0434\u0430 \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u043d\u044f\u043a\u043e\u0438, \u043a\u0430\u0442\u043e \u0433\u0438 \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0432 \u043f\u043e\u043b\u0435\u0442\u043e \u043f\u043e-\u0434\u043e\u043b\u0443 \u0438 \u0441\u043b\u0435\u0434 \u0442\u043e\u0432\u0430 \u043a\u043b\u0438\u043a\u043d\u0435\u0442\u0435 \u0432\u044a\u0440\u0445\u0443 \"\u0418\u0437\u0431\u043e\u0440\" \u0441\u0442\u0440\u0435\u043b\u043a\u0430 \u043c\u0435\u0436\u0434\u0443 \u0434\u0432\u0435\u0442\u0435 \u043a\u0443\u0442\u0438\u0438.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u0422\u043e\u0432\u0430 \u0435 \u0441\u043f\u0438\u0441\u044a\u043a \u043d\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438\u044f %s. \u041c\u043e\u0436\u0435\u0442\u0435 \u0434\u0430 \u043f\u0440\u0435\u043c\u0430\u0445\u043d\u0435\u0442\u0435 \u043d\u044f\u043a\u043e\u0438, \u043a\u0430\u0442\u043e \u0433\u0438 \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0432 \u043f\u043e\u043b\u0435\u0442\u043e \u043f\u043e-\u0434\u043e\u043b\u0443 \u0438 \u0441\u043b\u0435\u0434 \u0442\u043e\u0432\u0430 \u0449\u0440\u0430\u043a\u043d\u0435\u0442\u0435 \u0432\u044a\u0440\u0445\u0443 \"\u041f\u0440\u0435\u043c\u0430\u0445\u043d\u0438\" \u0441\u0442\u0440\u0435\u043b\u043a\u0430 \u043c\u0435\u0436\u0434\u0443 \u0434\u0432\u0435\u0442\u0435 \u043a\u0443\u0442\u0438\u0438.",
    "Today": "\u0414\u043d\u0435\u0441",
    "Tomorrow": "\u0423\u0442\u0440\u0435",
    "Type into this box to filter down the list of available %s.": "\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0432 \u0442\u043e\u0432\u0430 \u043f\u043e\u043b\u0435, \u0437\u0430 \u0434\u0430 \u0444\u0438\u043b\u0442\u0440\u0438\u0440\u0430\u0442\u0435 \u0441\u043f\u0438\u0441\u044a\u043a\u0430 \u043d\u0430 \u043d\u0430\u043b\u0438\u0447\u043d\u0438\u0442\u0435 %s.",
    "Yesterday": "\u0412\u0447\u0435\u0440\u0430",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0412\u0438\u0435 \u0441\u0442\u0435 \u0438\u0437\u0431\u0440\u0430\u043b\u0438 \u0434\u0430\u0434\u0435\u043d\u0430 \u0434\u0435\u0439\u043d\u043e\u0441\u0442, \u0430 \u043d\u0435 \u0441\u0442\u0435 \u043d\u0430\u043f\u0440\u0430\u0432\u0438\u043b\u0438 \u043d\u044f\u043a\u0430\u043a\u0432\u0438 \u043f\u0440\u043e\u043c\u0435\u043d\u0438 \u043f\u043e \u043f\u043e\u043b\u0435\u0442\u0430\u0442\u0430. \u0412\u0435\u0440\u043e\u044f\u0442\u043d\u043e \u0442\u044a\u0440\u0441\u0438\u0442\u0435 Go \u0431\u0443\u0442\u043e\u043d, \u0430 \u043d\u0435 \u0431\u0443\u0442\u043e\u043d\u0430 Save.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0412\u0438\u0435 \u0441\u0442\u0435 \u0438\u0437\u0431\u0440\u0430\u043b\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435, \u043d\u043e \u043d\u0435 \u0441\u0442\u0435 \u0437\u0430\u043f\u0438\u0441\u0430\u043b\u0438 \u043f\u0440\u043e\u043c\u0435\u043d\u0438\u0442\u0435 \u043f\u043e \u043f\u043e\u043b\u0435\u0442\u0430. \u041c\u043e\u043b\u044f, \u043a\u043b\u0438\u043a\u043d\u0435\u0442\u0435 \u041e\u041a, \u0437\u0430 \u0434\u0430 \u0441\u0435 \u0437\u0430\u043f\u0438\u0448\u0430\u0442. \u0422\u0440\u044f\u0431\u0432\u0430 \u043e\u0442\u043d\u043e\u0432\u043e \u0434\u0430 \u0437\u0430\u043f\u043e\u0447\u043d\u0435\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0418\u043c\u0430\u0442\u0435 \u043d\u0435\u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0438 \u043f\u0440\u043e\u043c\u0435\u043d\u0438 \u043f\u043e \u043e\u0442\u0434\u0435\u043b\u043d\u0438 \u043f\u043e\u043b\u0435\u0442\u0430 \u0437\u0430 \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u0430\u043d\u0435. \u0410\u043a\u043e \u0437\u0430\u043f\u043e\u0447\u043d\u0435\u0442\u0435 \u0434\u0440\u0443\u0433\u043e, \u043d\u0435\u0437\u0430\u043f\u0438\u0441\u0430\u043d\u0438\u0442\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u0438 \u0449\u0435 \u0431\u044a\u0434\u0430\u0442 \u0437\u0430\u0433\u0443\u0431\u0435\u043d\u0438.",
    "one letter Friday\u0004F": "\u041f",
    "one letter Monday\u0004M": "\u041f",
    "one letter Saturday\u0004S": "\u0421",
    "one letter Sunday\u0004S": "\u041d",
    "one letter Thursday\u0004T": "\u0427",
    "one letter Tuesday\u0004T": "\u0412",
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
    "SHORT_DATE_FORMAT": "d.m.Y",
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

