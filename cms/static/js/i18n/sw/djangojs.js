

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
      "umechagua %(sel)s kati ya %(cnt)s",
      "umechagua %(sel)s kati ya %(cnt)s"
    ],
    "6 a.m.": "Saa 12 alfajiri",
    "Available %s": "Yaliyomo: %s",
    "Cancel": "Ghairi",
    "Choose": "Chagua",
    "Choose a time": "Chagua wakati",
    "Choose all": "Chagua vyote",
    "Chosen %s": "Chaguo la %s",
    "Click to choose all %s at once.": "Bofya kuchagua %s kwa pamoja.",
    "Click to remove all chosen %s at once.": "Bofya ili kuondoa %s chaguliwa kwa pamoja.",
    "Filter": "Chuja",
    "Hide": "Ficha",
    "Midnight": "Usiku wa manane",
    "Noon": "Adhuhuri",
    "Note: You are %s hour ahead of server time.": [
      "Kumbuka: Uko saa %s mbele ukilinganisha na majira ya seva",
      "Kumbuka: Uko masaa %s mbele ukilinganisha na majira ya seva"
    ],
    "Note: You are %s hour behind server time.": [
      "Kumbuka: Uko saa %s nyuma ukilinganisha na majira ya seva",
      "Kumbuka: Uko masaa %s nyuma ukilinganisha na majira ya seva"
    ],
    "Now": "Sasa",
    "Remove": "Ondoa",
    "Remove all": "Ondoa vyote",
    "Show": "Onesha",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Hii ni orodha ya %s uliyochagua. Unaweza kuchagua baadhi vitu kwa kuvichagua katika kisanduku hapo chini kisha kubofya mshale wa \"Chagua\" kati ya visanduku viwili.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Hii ni orodha ya %s uliyochagua. Unaweza kuondoa baadhi vitu kwa kuvichagua katika kisanduku hapo chini kisha kubofya mshale wa \"Ondoa\" kati ya visanduku viwili.",
    "Today": "Leo",
    "Tomorrow": "Kesho",
    "Type into this box to filter down the list of available %s.": "Chapisha katika kisanduku hiki ili kuchuja orodha ya %s iliyopo.",
    "Yesterday": "Jana",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Umechagua tendo, lakini bado hujahifadhi mabadiliko yako katika uga husika.  Inawezekana unatafuta kitufe cha Nenda badala ya Hifadhi",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Umechagua tendo, lakini bado hujahifadhi mabadiliko yako katika uga husika. Tafadali bofya Sawa ukitaka kuhifadhi. Utahitajika kufanya upya kitendo ",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Umeacha kuhifadhi mabadiliko katika uga zinazoharirika. Ikiwa utafanya tendo lingine, mabadiliko ambayo hayajahifadhiwa yatapotea."
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

