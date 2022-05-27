

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
      "%(cnt)s \u0915\u094b %(sel)s \u091a\u092f\u0928 \u0917\u0930\u093f\u092f\u094b",
      "%(cnt)s \u0915\u094b %(sel)s \u091a\u092f\u0928 \u0917\u0930\u093f\u092f\u094b"
    ],
    "6 a.m.": "\u092c\u093f\u0939\u093e\u0928 \u096c \u092c\u091c\u0947",
    "6 p.m.": "\u092c\u0947\u0932\u0941\u0915\u0940 \u096c \u092c\u091c\u0947",
    "Available %s": "\u0909\u092a\u0932\u092c\u094d\u0927 %s",
    "Cancel": "\u0930\u0926\u094d\u0926 \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938 ",
    "Choose": "\u091b\u093e\u0928\u094d\u0928\u0941\u0939\u094b\u0938 ",
    "Choose a Date": "\u092e\u093f\u0924\u093f \u091b\u093e\u0928\u094d\u0928\u0941 \u0939\u094b\u0938 \u0964",
    "Choose a Time": "\u0938\u092e\u092f \u091b\u093e\u0928\u094d\u0928\u0941 \u0939\u094b\u0938 \u0964",
    "Choose a time": "\u0938\u092e\u092f \u091a\u092f\u0928 \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938",
    "Choose all": "\u0938\u092c\u0948 \u091b\u093e\u0928\u094d\u0928\u0941\u0939\u094b\u0938 ",
    "Chosen %s": "\u091b\u093e\u0928\u093f\u090f\u0915\u094b %s",
    "Click to choose all %s at once.": "\u090f\u0915\u0948 \u0915\u094d\u0932\u093f\u0915\u092e\u093e \u0938\u092c\u0948 %s \u091b\u093e\u0928\u094d\u0928\u0941\u0939\u094b\u0938 ",
    "Click to remove all chosen %s at once.": "\u090f\u0915\u0948 \u0915\u094d\u0932\u093f\u0915\u092e\u093e \u0938\u092c\u0948 \u091b\u093e\u0928\u093f\u090f\u0915\u093e %s \u0939\u091f\u093e\u0909\u0928\u0941\u0939\u094b\u0938 \u0964",
    "Filter": "\u091b\u093e\u0928\u094d\u0928\u0941\u0939\u094b\u0938",
    "Hide": "\u0932\u0941\u0915\u093e\u0909\u0928\u0941\u0939\u094b\u0938 ",
    "Midnight": "\u092e\u0927\u094d\u092f\u0930\u093e\u0924",
    "Noon": "\u092e\u0927\u094d\u092f\u093e\u0928\u094d\u0939",
    "Note: You are %s hour ahead of server time.": [
      "\u0938\u0942\u091a\u0928\u093e: \u0924\u092a\u093e\u0908\u0901 \u0938\u0930\u094d\u092d\u0930 \u0938\u092e\u092f \u092d\u0928\u094d\u0926\u093e %s \u0918\u0923\u094d\u091f\u093e \u0905\u0917\u093e\u0921\u093f \u0939\u0941\u0928\u0941\u0939\u0941\u0928\u094d\u091b \u0964",
      "\u0938\u0942\u091a\u0928\u093e: \u0924\u092a\u093e\u0908\u0901 \u0938\u0930\u094d\u092d\u0930 \u0938\u092e\u092f \u092d\u0928\u094d\u0926\u093e %s \u0918\u0923\u094d\u091f\u093e \u0905\u0917\u093e\u0921\u093f \u0939\u0941\u0928\u0941\u0939\u0941\u0928\u094d\u091b \u0964"
    ],
    "Note: You are %s hour behind server time.": [
      "\u0938\u0942\u091a\u0928\u093e: \u0924\u092a\u093e\u0908\u0901 \u0938\u0930\u094d\u092d\u0930 \u0938\u092e\u092f \u092d\u0928\u094d\u0926\u093e %s \u0918\u0923\u094d\u091f\u093e \u092a\u091b\u093e\u0921\u093f \u0939\u0941\u0928\u0941\u0939\u0941\u0928\u094d\u091b \u0964",
      "\u0938\u0942\u091a\u0928\u093e: \u0924\u092a\u093e\u0908\u0901 \u0938\u0930\u094d\u092d\u0930 \u0938\u092e\u092f \u092d\u0928\u094d\u0926\u093e %s \u0918\u0923\u094d\u091f\u093e \u092a\u091b\u093e\u0921\u093f \u0939\u0941\u0928\u0941\u0939\u0941\u0928\u094d\u091b \u0964"
    ],
    "Now": "\u092f\u0924\u093f\u0916\u0947\u0930",
    "Remove": "\u0939\u091f\u093e\u0909\u0928\u0941\u0939\u094b\u0938",
    "Remove all": "\u0938\u092c\u0948 \u0939\u091f\u093e\u0909\u0928\u0941\u0939\u094b\u0938 ",
    "Show": "\u0926\u0947\u0916\u093e\u0909\u0928\u0941\u0939\u094b\u0938 ",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u092f\u094b \u0909\u092a\u0932\u092c\u094d\u0927 %s \u0915\u094b \u0938\u0941\u091a\u0940 \u0939\u094b\u0964 \u0924\u092a\u093e\u0908\u0902\u0932\u0947 \u092f\u0940 \u092e\u0927\u094d\u092f \u0915\u0947\u0939\u0940 \u092c\u0915\u094d\u0938\u092c\u093e\u091f \u091a\u092f\u0928 \u0917\u0930\u0940 \u092c\u0915\u094d\u0938 \u092c\u0940\u091a\u094d\u0915\u094b \"\u091b\u093e\u0928\u094d\u0928\u0941\u0939\u094b\u0938 \" \u0924\u0940\u0930\u092e\u093e \u0915\u094d\u0932\u093f\u0915 \u0917\u0930\u0940 \u091b\u093e\u0928\u094d\u0928\u0938\u0915\u094d\u0928\u0941\u0939\u0941\u0928\u094d\u091b \u0964 ",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u092f\u094b \u091b\u093e\u0928\u093f\u090f\u0915\u093e %s \u0915\u094b \u0938\u0941\u091a\u0940 \u0939\u094b \u0964 \u0924\u092a\u093e\u0908\u0902\u0932\u0947 \u092f\u0940 \u092e\u0927\u094d\u092f \u0915\u0947\u0939\u0940 \u092c\u0915\u094d\u0938\u092c\u093e\u091f \u091a\u092f\u0928 \u0917\u0930\u0940 \u092c\u0915\u094d\u0938 \u092c\u0940\u091a\u094d\u0915\u094b \"\u0939\u091f\u093e\u0909\u0928\u0941\u0939\u094b\u0938\" \u0924\u0940\u0930\u092e\u093e \u0915\u094d\u0932\u093f\u0915 \u0917\u0930\u0940 \u0939\u091f\u093e\u0909\u0928 \u0938\u0915\u094d\u0928\u0941\u0939\u0941\u0928\u094d\u091b \u0964 ",
    "Today": "\u0906\u091c",
    "Tomorrow": "\u092d\u094b\u0932\u093f",
    "Type into this box to filter down the list of available %s.": " \u0909\u092a\u0932\u092c\u094d\u0927 %s \u0915\u094b \u0938\u0941\u091a\u093f\u092c\u093e\u091f \u091b\u093e\u0928\u094d\u0928 \u092f\u094b \u092c\u0915\u094d\u0938\u092e\u093e \u091f\u093e\u0907\u092a \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938 ",
    "Yesterday": "\u0939\u093f\u091c\u094b",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0924\u092a\u093e\u0907\u0932\u0947 \u0915\u093e\u0930\u094d\u092f \u091b\u093e\u0928\u0947 \u092a\u0928\u093f \u092b\u093e\u0901\u091f\u0939\u0930\u0941\u092e\u093e \u092b\u0947\u0930\u092c\u0926\u0932\u0939\u0930\u0941 \u0917\u0930\u094d\u0928\u0941 \u092d\u090f\u0915\u094b \u091b\u0948\u0928 \u0964 \u092c\u091a\u0924 \u0917\u0930\u094d\u0928\u0941 \u092d\u0928\u094d\u0926\u093e \u092a\u0928\u093f \u0905\u0918\u093f \u092c\u0922\u094d\u0928\u0941\u0939\u094b\u0938 \u0964",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0924\u092a\u093e\u0907\u0932\u0947 \u0915\u093e\u0930\u094d\u092f \u091b\u093e\u0928\u0947 \u092a\u0928\u093f \u092b\u0947\u0930\u092c\u0926\u0932\u0939\u0930\u0941 \u092c\u091a\u0924 \u0917\u0930\u094d\u0928\u0941 \u092d\u090f\u0915\u094b \u091b\u0948\u0928 \u0964 \u0915\u0943\u092a\u092f\u093e \u092c\u091a\u0924 \u0917\u0930\u094d\u0928 \u0939\u0941\u0928\u094d\u091b \u0925\u093f\u091a\u094d\u0928\u0941\u0939\u094b\u0938 \u0964 \u0915\u093e\u0930\u094d\u092f \u092a\u0941\u0928: \u0938\u091e\u094d\u091a\u093e\u0932\u0928 \u0917\u0930\u094d\u0928\u0941\u092a\u0930\u094d\u0928\u0947\u091b \u0964",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0924\u092a\u093e\u0907\u0915\u094b \u092b\u0947\u0930\u092c\u0926\u0932 \u092c\u091a\u0924 \u092d\u090f\u0915\u094b \u091b\u0948\u0928 \u0964 \u0915\u093e\u0930\u094d\u092f \u092d\u090f\u092e\u093e \u092c\u091a\u0924 \u0928\u092d\u090f\u0915\u093e \u092b\u0947\u0930\u092c\u0926\u0932 \u0939\u0930\u093e\u0909\u0928\u0947 \u091b\u0928\u094d \u0964"
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

