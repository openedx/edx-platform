

(function (globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function (n) {
    var v=(n != 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  
  /* gettext library */

  django.catalog = {
    "%d month": [
      "%d \u05d7\u05d5\u05d3\u05e9", 
      "%d \u05d7\u05d5\u05d3\u05e9\u05d9\u05dd"
    ], 
    "%d year": [
      "%d \u05e9\u05e0\u05d4", 
      "%d \u05e9\u05e0\u05d9\u05dd"
    ], 
    "Answer:": "\u05ea\u05e9\u05d5\u05d1\u05d4:", 
    "Bold": "\u05de\u05d5\u05d3\u05d2\u05e9", 
    "Delete this %(item_display_name)s?": "\u05de\u05d7\u05e7 \u05d0\u05ea \u05d4%(item_display_name)s?", 
    "Short explanation": "\u05d4\u05e1\u05d1\u05e8 \u05e7\u05e6\u05e8", 
    "Strikethrough": "\u05e7\u05d5 \u05d7\u05d5\u05e6\u05d4", 
    "Subscript": "\u05db\u05ea\u05d1 \u05ea\u05d7\u05ea\u05d9", 
    "Superscript": "\u05db\u05ea\u05d1 \u05e2\u05d9\u05dc\u05d9", 
    "Table": "\u05d8\u05d1\u05dc\u05d4", 
    "Table properties": "\u05de\u05d0\u05e4\u05d9\u05d9\u05e0\u05d9 \u05d8\u05d1\u05dc\u05d4", 
    "Title": "\u05db\u05d5\u05ea\u05e8\u05ea", 
    "Tools": "\u05db\u05dc\u05d9\u05dd", 
    "Yes, delete this %(xblock_type)s": "\u05db\u05df, \u05de\u05d7\u05e7 \u05d0\u05ea %(xblock_type)s", 
    "You have unsaved changes are you sure you want to navigate away?": "\u05d9\u05e9\u05e0\u05dd \u05e9\u05d9\u05e0\u05d5\u05d9\u05d9\u05dd \u05e9\u05dc\u05d0 \u05e0\u05e9\u05de\u05e8\u05d5, \u05d4\u05d0\u05dd \u05d0\u05ea\u05d4 \u05d1\u05d8\u05d5\u05d7 \u05e9\u05d0\u05ea\u05d4 \u05e8\u05d5\u05e6\u05d4 \u05dc\u05e2\u05d6\u05d5\u05d1?", 
    "answer": "\u05ea\u05e9\u05d5\u05d1\u05d4"
  };

  django.gettext = function (msgid) {
    var value = django.catalog[msgid];
    if (typeof(value) == 'undefined') {
      return msgid;
    } else {
      return (typeof(value) == 'string') ? value : value[0];
    }
  };

  django.ngettext = function (singular, plural, count) {
    var value = django.catalog[singular];
    if (typeof(value) == 'undefined') {
      return (count == 1) ? singular : plural;
    } else {
      return value[django.pluralidx(count)];
    }
  };

  django.gettext_noop = function (msgid) { return msgid; };

  django.pgettext = function (context, msgid) {
    var value = django.gettext(context + '\x04' + msgid);
    if (value.indexOf('\x04') != -1) {
      value = msgid;
    }
    return value;
  };

  django.npgettext = function (context, singular, plural, count) {
    var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
    if (value.indexOf('\x04') != -1) {
      value = django.ngettext(singular, plural, count);
    }
    return value;
  };
  

  django.interpolate = function (fmt, obj, named) {
    if (named) {
      return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
    } else {
      return fmt.replace(/%s/g, function(match){return String(obj.shift())});
    }
  };


  /* formatting library */

  django.formats = {
    "DATETIME_FORMAT": "j \u05d1F Y H:i", 
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
    "DATE_FORMAT": "j \u05d1F Y", 
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
    "MONTH_DAY_FORMAT": "j \u05d1F", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "d/m/Y H:i", 
    "SHORT_DATE_FORMAT": "d/m/Y", 
    "THOUSAND_SEPARATOR": ",", 
    "TIME_FORMAT": "H:i", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M:%S.%f", 
      "%H:%M"
    ], 
    "YEAR_MONTH_FORMAT": "F Y"
  };

  django.get_format = function (format_type) {
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

}(this));

