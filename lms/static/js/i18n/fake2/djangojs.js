

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
    "Grade must be a number.": "\u01e4\u0279\u0250d\u01dd \u026fns\u0287 b\u01dd \u0250 nn\u026fb\u01dd\u0279.",
    "Grade must be an integer.": "\u01e4\u0279\u0250d\u01dd \u026fns\u0287 b\u01dd \u0250n \u1d09n\u0287\u01dd\u0183\u01dd\u0279.",
    "Grade must be positive.": "\u01e4\u0279\u0250d\u01dd \u026fns\u0287 b\u01dd d\u00f8s\u1d09\u0287\u1d09\u028c\u01dd.",
    "Maximum score is %(max_score)s": "M\u0250x\u1d09\u026fn\u026f s\u0254\u00f8\u0279\u01dd \u1d09s %(max_score)s",
    "No grade to remove.": "N\u00f8 \u0183\u0279\u0250d\u01dd \u0287\u00f8 \u0279\u01dd\u026f\u00f8\u028c\u01dd.",
    "The file you are trying to upload is too large.": "\u0166\u0265\u01dd \u025f\u1d09l\u01dd \u028e\u00f8n \u0250\u0279\u01dd \u0287\u0279\u028e\u1d09n\u0183 \u0287\u00f8 ndl\u00f8\u0250d \u1d09s \u0287\u00f8\u00f8 l\u0250\u0279\u0183\u01dd.",
    "There was an error uploading your file.": "\u0166\u0265\u01dd\u0279\u01dd \u028d\u0250s \u0250n \u01dd\u0279\u0279\u00f8\u0279 ndl\u00f8\u0250d\u1d09n\u0183 \u028e\u00f8n\u0279 \u025f\u1d09l\u01dd.",
    "Upload %(file_name)s": "\u0244dl\u00f8\u0250d %(file_name)s",
    "Uploading...": "\u0244dl\u00f8\u0250d\u1d09n\u0183...",
    "Uploading... %(percent)s %": "\u0244dl\u00f8\u0250d\u1d09n\u0183... %(percent)s %"
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
    "DATE_FORMAT": "N j, Y",
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
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "F j",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "m/d/Y P",
    "SHORT_DATE_FORMAT": "m/d/Y",
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

