

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
      "%(sel)s \u044d\u044d\u0441 %(cnt)s \u0441\u043e\u043d\u0433\u043e\u0441\u043e\u043d", 
      "%(sel)s \u044d\u044d\u0441 %(cnt)s \u0441\u043e\u043d\u0433\u043e\u0441\u043e\u043d"
    ], 
    "6 a.m.": "6 \u0446\u0430\u0433", 
    "6 p.m.": "\u041e\u0440\u043e\u0439\u043d 6 \u0446\u0430\u0433", 
    "Available %s": "\u0411\u043e\u043b\u043e\u043c\u0436\u0442\u043e\u0439 %s", 
    "Cancel": "\u0411\u043e\u043b\u0438\u0445", 
    "Choose": "\u0421\u043e\u043d\u0433\u043e\u0445", 
    "Choose a Date": "\u04e8\u0434\u04e9\u0440 \u0441\u043e\u043d\u0433\u043e\u0445", 
    "Choose a Time": "\u0426\u0430\u0433 \u0441\u043e\u043d\u0433\u043e\u0445", 
    "Choose a time": "\u0426\u0430\u0433 \u0441\u043e\u043d\u0433\u043e\u0445", 
    "Choose all": "\u0411\u04af\u0433\u0434\u0438\u0439\u0433 \u043d\u044c \u0441\u043e\u043d\u0433\u043e\u0445", 
    "Chosen %s": "\u0421\u043e\u043d\u0433\u043e\u0433\u0434\u0441\u043e\u043d %s", 
    "Click to choose all %s at once.": "\u0411\u04af\u0433\u0434\u0438\u0439\u0433 \u0441\u043e\u043d\u0433\u043e\u0445 \u0431\u043e\u043b %s \u0434\u0430\u0440\u043d\u0430 \u0443\u0443", 
    "Click to remove all chosen %s at once.": "%s \u0438\u0439\u043d \u0441\u043e\u043d\u0433\u043e\u043e\u0434 \u0431\u04af\u0433\u0434\u0438\u0439\u0433 \u043d\u044c \u0430\u0440\u0438\u043b\u0433\u0430\u043d\u0430", 
    "Filter": "\u0428\u04af\u04af\u043b\u0442\u04af\u04af\u0440", 
    "Hide": "\u041d\u0443\u0443\u0445", 
    "Midnight": "\u0428\u04e9\u043d\u04e9 \u0434\u0443\u043d\u0434", 
    "Noon": "\u04ae\u0434 \u0434\u0443\u043d\u0434", 
    "Note: You are %s hour ahead of server time.": [
      "\u0422\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0438\u0439\u043d \u0446\u0430\u0433\u0430\u0430\u0441 %s \u0446\u0430\u0433\u0438\u0439\u043d \u0442\u04af\u0440\u04af\u04af\u043d\u0434 \u044f\u0432\u0436 \u0431\u0430\u0439\u043d\u0430", 
      "\u0422\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0438\u0439\u043d \u0446\u0430\u0433\u0430\u0430\u0441 %s \u0446\u0430\u0433\u0438\u0439\u043d \u0442\u04af\u0440\u04af\u04af\u043d\u0434 \u044f\u0432\u0436 \u0431\u0430\u0439\u043d\u0430"
    ], 
    "Note: You are %s hour behind server time.": [
      "\u0422\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0438\u0439\u043d \u0446\u0430\u0433\u0430\u0430\u0441 %s \u0446\u0430\u0433\u0430\u0430\u0440 \u0445\u043e\u0446\u043e\u0440\u0447 \u0431\u0430\u0439\u043d\u0430", 
      "\u0422\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0438\u0439\u043d \u0446\u0430\u0433\u0430\u0430\u0441 %s \u0446\u0430\u0433\u0430\u0430\u0440 \u0445\u043e\u0446\u043e\u0440\u0447 \u0431\u0430\u0439\u043d\u0430"
    ], 
    "Now": "\u041e\u0434\u043e\u043e", 
    "Remove": "\u0425\u0430\u0441", 
    "Remove all": "\u0411\u04af\u0433\u0434\u0438\u0439\u0433 \u0430\u0440\u0438\u043b\u0433\u0430\u0445", 
    "Show": "\u04ae\u0437\u044d\u0445", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u042d\u043d\u044d %s \u0436\u0430\u0433\u0441\u0430\u0430\u043b\u0442 \u043d\u044c \u0431\u043e\u043b\u043e\u043c\u0436\u0438\u0442 \u0443\u0442\u0433\u044b\u043d \u0436\u0430\u0433\u0441\u0430\u0430\u043b\u0442. \u0422\u0430 \u0430\u043b\u044c \u043d\u044d\u0433\u0438\u0439\u0433 \u043d\u044c \u0441\u043e\u043d\u0433\u043e\u043e\u0434 \"\u0421\u043e\u043d\u0433\u043e\u0445\" \u0434\u044d\u044d\u0440 \u0434\u0430\u0440\u0436 \u043d\u04e9\u0433\u04e9\u04e9 \u0445\u044d\u0441\u044d\u0433\u0442 \u043e\u0440\u0443\u0443\u043b\u0430\u0445 \u0431\u043e\u043b\u043e\u043c\u0436\u0442\u043e\u0439.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u042d\u043d\u044d %s \u0441\u043e\u043d\u0433\u043e\u0433\u0434\u0441\u043e\u043d \u0443\u0442\u0433\u0443\u0443\u0434\u044b\u0433 \u0436\u0430\u0433\u0441\u0430\u0430\u043b\u0442. \u0422\u0430 \u0430\u043b\u044c \u043d\u044d\u0433\u0438\u0439\u0433 \u043d\u044c \u0445\u0430\u0441\u0430\u0445\u044b\u0433 \u0445\u04af\u0441\u0432\u044d\u043b \u0441\u043e\u043d\u0433\u043e\u043e\u0445 \"\u0425\u0430\u0441\" \u0434\u044d\u044d\u0440 \u0434\u0430\u0440\u043d\u0430 \u0443\u0443.", 
    "This response could not be saved.": "\u0425\u0430\u0440\u0438\u0443\u043b\u0442 \u0445\u0430\u043b\u0433\u0430\u043b\u0430\u0433\u0434\u0441\u0430\u043d\u0433\u04af\u0439.", 
    "Today": "\u04e8\u043d\u04e9\u04e9\u0434\u04e9\u0440", 
    "Tomorrow": "\u041c\u0430\u0440\u0433\u0430\u0430\u0448", 
    "Type into this box to filter down the list of available %s.": "\u042d\u043d\u044d \u043d\u04af\u0434\u044d\u043d\u0434 \u0431\u0438\u0447\u044d\u044d\u0434 \u0434\u0430\u0440\u0430\u0430\u0445 %s \u0436\u0430\u0433\u0441\u0430\u0430\u043b\u0442\u0430\u0430\u0441 \u0448\u04af\u04af\u043d\u044d \u04af\u04af. ", 
    "Yesterday": "\u04e8\u0447\u0438\u0433\u0434\u04e9\u0440", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0422\u0430 1 \u04af\u0439\u043b\u0434\u043b\u0438\u0439\u0433 \u0441\u043e\u043d\u0433\u043e\u0441\u043e\u043d \u0431\u0430\u0439\u043d\u0430 \u0431\u0430\u0441 \u0442\u0430 \u044f\u043c\u0430\u0440\u0432\u0430\u0430 \u04e9\u04e9\u0440\u0447\u043b\u04e9\u043b\u0442 \u043e\u0440\u0443\u0443\u043b\u0441\u0430\u043d\u0433\u04af\u0439. \u0422\u0430 Save \u0442\u043e\u0432\u0447\u043b\u0443\u0443\u0440 \u0431\u0438\u0448 Go \u0442\u043e\u0432\u0447\u043b\u0443\u0443\u0440\u044b\u0433 \u0445\u0430\u0439\u0436 \u0431\u0430\u0439\u0433\u0430\u0430 \u0431\u043e\u043b\u043e\u043b\u0442\u043e\u0439.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0422\u0430 1 \u04af\u0439\u043b\u0434\u043b\u0438\u0439\u0433 \u0441\u043e\u043d\u0433\u043e\u0441\u043e\u043d \u0431\u0430\u0439\u043d\u0430, \u0433\u044d\u0432\u0447 \u0442\u0430 \u04e9\u04e9\u0440\u0438\u0439\u043d \u04e9\u04e9\u0440\u0447\u043b\u04e9\u043b\u0442\u04af\u04af\u0434\u044d\u044d \u0442\u043e\u0434\u043e\u0440\u0445\u043e\u0439 \u0442\u0430\u043b\u0431\u0430\u0440\u0443\u0443\u0434\u0430\u0434 \u043d\u044c \u043e\u0440\u0443\u0443\u043b\u0430\u0433\u04af\u0439 \u0431\u0430\u0439\u043d\u0430. OK \u0434\u0430\u0440\u0436 \u0441\u0430\u043d\u0443\u0443\u043b\u043d\u0430 \u0443\u0443. \u042d\u043d\u044d \u04af\u0439\u043b\u0434\u043b\u0438\u0439\u0433 \u0442\u0430 \u0434\u0430\u0445\u0438\u043d \u0445\u0438\u0439\u0445 \u0448\u0430\u0430\u0440\u0434\u043b\u0430\u0433\u0430\u0442\u0430\u0439.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0425\u0430\u0434\u0433\u0430\u043b\u0430\u0430\u0433\u04af\u0439 \u04e9\u04e9\u0440\u0447\u043b\u04e9\u043b\u0442\u04af\u04af\u0434 \u0431\u0430\u0439\u043d\u0430. \u042d\u043d\u044d \u04af\u0439\u043b\u0434\u044d\u043b\u0438\u0439\u0433 \u0445\u0438\u0439\u0432\u044d\u043b \u04e9\u04e9\u0440\u0447\u043b\u04e9\u043b\u0442\u04af\u04af\u0434 \u0443\u0441\u0442\u0430\u0445 \u0431\u043e\u043b\u043d\u043e."
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
        return value[django.pluralidx(count)];
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
    "DATETIME_FORMAT": "N j, Y, P", 
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
    "DECIMAL_SEPARATOR": ".", 
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "F j", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "m/d/Y P", 
    "SHORT_DATE_FORMAT": "j M Y", 
    "THOUSAND_SEPARATOR": ",", 
    "TIME_FORMAT": "g:i A", 
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

