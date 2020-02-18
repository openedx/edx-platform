

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
      "%(cnt)s \u092e\u0947\u0902 \u0938\u0947 %(sel)s \u091a\u0941\u0928\u093e \u0917\u092f\u093e \u0939\u0948\u0902", 
      "%(cnt)s \u092e\u0947\u0902 \u0938\u0947 %(sel)s \u091a\u0941\u0928\u0947 \u0917\u090f \u0939\u0948\u0902"
    ], 
    "6 a.m.": "\u0938\u0941\u092c\u0939 6 \u092c\u091c\u0947", 
    "Available %s": "\u0909\u092a\u0932\u092c\u094d\u0927 %s", 
    "Cancel": "\u0930\u0926\u094d\u0926 \u0915\u0930\u0947\u0902", 
    "Choose": "\u091a\u0941\u0928\u0947\u0902", 
    "Choose a time": "\u090f\u0915 \u0938\u092e\u092f \u091a\u0941\u0928\u0947\u0902", 
    "Choose all": "\u0938\u092d\u0940 \u091a\u0941\u0928\u0947\u0902", 
    "Chosen %s": "\u091a\u0941\u0928\u0947\u0902 %s", 
    "Click to choose all %s at once.": "\u090f\u0915 \u0939\u0940 \u092c\u093e\u0930 \u092e\u0947\u0902 \u0938\u092d\u0940 %s \u0915\u094b \u091a\u0941\u0928\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0915\u094d\u0932\u093f\u0915 \u0915\u0930\u0947\u0902.", 
    "Click to remove all chosen %s at once.": "\u090f\u0915 \u0939\u0940 \u092c\u093e\u0930 \u092e\u0947\u0902 \u0938\u092d\u0940 %s \u0915\u094b \u0939\u091f\u093e\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0915\u094d\u0932\u093f\u0915 \u0915\u0930\u0947\u0902.", 
    "Could not retrieve upload url.": "\u0905\u092a\u0932\u094b\u0921 \u092f\u0942.\u0906\u0930.\u0910\u0932. \u092a\u094d\u0930\u093e\u092a\u094d\u0924 \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "Filter": "\u091b\u093e\u0928\u0928\u093e", 
    "Hide": "  \u091b\u093f\u092a\u093e\u0913", 
    "Midnight": "\u092e\u0927\u094d\u092f\u0930\u093e\u0924\u094d\u0930\u0940", 
    "Noon": "\u0926\u094b\u092a\u0939\u0930", 
    "Now": "\u0905\u092c", 
    "One or more rescheduling tasks failed.": "\u090f\u0915 \u092f\u093e \u0905\u0927\u093f\u0915 \u092a\u0941\u0928\u0930\u094d\u0928\u093f\u0930\u094d\u0927\u093e\u0930\u0923 \u0915\u093e\u0930\u094d\u092f \u0935\u093f\u092b\u0932 \u0930\u0939\u0947.", 
    "Remove": "\u0939\u091f\u093e\u0928\u093e", 
    "Remove all": "\u0938\u092d\u0940 \u0915\u094b \u0939\u091f\u093e\u090f\u0901", 
    "Saving...": "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0915\u093f\u092f\u093e \u091c\u093e \u0930\u0939\u093e \u0939\u0948 ...", 
    "Show": "\u0926\u093f\u0916\u093e\u0913", 
    "This assessment could not be submitted.": "\u0907\u0938 \u092e\u0942\u0932\u094d\u092f\u093e\u0902\u0915\u0928 \u0915\u094b \u091c\u092e\u093e \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "This feedback could not be submitted.": "\u0907\u0938 \u092a\u094d\u0930\u0924\u093f\u0915\u094d\u0930\u093f\u092f\u093e \u0915\u094b \u091c\u092e\u093e \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u092f\u0939 \u0909\u092a\u0932\u092c\u094d\u0927 %s \u0915\u0940 \u0938\u0942\u091a\u0940 \u0939\u0948. \u0906\u092a \u0909\u0928\u094d\u0939\u0947\u0902 \u0928\u0940\u091a\u0947 \u0926\u093f\u090f \u0917\u090f \u092c\u0949\u0915\u094d\u0938 \u092e\u0947\u0902 \u0938\u0947 \u091a\u092f\u0928 \u0915\u0930\u0915\u0947 \u0915\u0941\u091b \u0915\u094b \u091a\u0941\u0928 \u0938\u0915\u0924\u0947 \u0939\u0948\u0902 \u0914\u0930 \u0909\u0938\u0915\u0947 \u092c\u093e\u0926 \u0926\u094b \u092c\u0949\u0915\u094d\u0938 \u0915\u0947 \u092c\u0940\u091a \"\u091a\u0941\u0928\u0947\u0902\" \u0924\u0940\u0930 \u092a\u0930 \u0915\u094d\u0932\u093f\u0915 \u0915\u0930\u0947\u0902.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u092f\u0939 \u0909\u092a\u0932\u092c\u094d\u0927 %s \u0915\u0940 \u0938\u0942\u091a\u0940 \u0939\u0948. \u0906\u092a \u0909\u0928\u094d\u0939\u0947\u0902 \u0928\u0940\u091a\u0947 \u0926\u093f\u090f \u0917\u090f \u092c\u0949\u0915\u094d\u0938 \u092e\u0947\u0902 \u0938\u0947 \u091a\u092f\u0928 \u0915\u0930\u0915\u0947 \u0915\u0941\u091b \u0915\u094b \u0939\u091f\u093e \u0938\u0915\u0924\u0947 \u0939\u0948\u0902 \u0914\u0930 \u0909\u0938\u0915\u0947 \u092c\u093e\u0926 \u0926\u094b \u092c\u0949\u0915\u094d\u0938 \u0915\u0947 \u092c\u0940\u091a \"\u0939\u091f\u093e\u092f\u0947\u0902\" \u0924\u0940\u0930 \u092a\u0930 \u0915\u094d\u0932\u093f\u0915 \u0915\u0930\u0947\u0902.", 
    "This problem could not be saved.": "\u0907\u0938 \u092a\u094d\u0930\u0936\u094d\u0928 \u0915\u094b \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "This response could not be saved.": "\u0907\u0938 \u0909\u0924\u094d\u0924\u0930 \u0915\u094b \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "This response could not be submitted.": "\u0907\u0938 \u0909\u0924\u094d\u0924\u0930 \u0915\u094b \u091c\u092e\u093e \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "This section could not be loaded.": "\u092f\u0939 \u0916\u0902\u0921 \u0932\u094b\u0921 \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u093e \u091c\u093e \u0938\u0915\u093e.", 
    "Today": "\u0906\u091c", 
    "Tomorrow": "\u0915\u0932", 
    "Type into this box to filter down the list of available %s.": "\u0907\u0938 \u092c\u0949\u0915\u094d\u0938 \u092e\u0947\u0902 \u091f\u093e\u0907\u092a \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0928\u0940\u091a\u0947 \u0909\u092a\u0932\u092c\u094d\u0927 %s \u0915\u0940 \u0938\u0942\u091a\u0940 \u0915\u094b \u092b\u093c\u093f\u0932\u094d\u091f\u0930 \u0915\u0930\u0947\u0902.", 
    "Yesterday": "\u0915\u0932 (\u092c\u0940\u0924\u093e)", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0906\u092a \u0928\u0947 \u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908 \u091a\u0941\u0928\u0940 \u0939\u0948\u0902, \u0914\u0930 \u0906\u092a \u0928\u0947 \u0938\u094d\u0935\u0924\u0902\u0924\u094d\u0930 \u0938\u092e\u094d\u092a\u093e\u0926\u0928\u0915\u094d\u0937\u092e \u0915\u094d\u0937\u0947\u0924\u094d\u0930/\u0938\u094d\u0924\u092e\u094d\u092d \u092e\u0947\u0902 \u092c\u0926\u0932 \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u0947 \u0939\u0948\u0902|  \u0938\u0902\u092d\u0935\u0924\u0903 '\u0938\u0947\u0935' \u092c\u091f\u0928 \u0915\u0947 \u092c\u091c\u093e\u092f \u0906\u092a '\u0917\u094b' \u092c\u091f\u0928 \u0922\u0942\u0928\u094d\u0922 \u0930\u0939\u0947 \u0939\u094b |", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0906\u092a \u0928\u0947 \u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908 \u0924\u094b \u091a\u0941\u0928\u0940 \u0939\u0948\u0902, \u092a\u0930 \u0938\u094d\u0935\u0924\u0902\u0924\u094d\u0930 \u0938\u092e\u094d\u092a\u093e\u0926\u0928\u0915\u094d\u0937\u092e \u0915\u094d\u0937\u0947\u0924\u094d\u0930/\u0938\u094d\u0924\u092e\u094d\u092d \u092e\u0947\u0902 \u0915\u093f\u092f\u0947 \u0939\u0941\u090f \u092c\u0926\u0932 \u0905\u092d\u0940 \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0928\u0939\u0940\u0902 \u0915\u093f\u092f\u0947 \u0939\u0948\u0902| \u0909\u0928\u094d\u0939\u0947\u0902 \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0915\u0943\u092a\u092f\u093e '\u0913\u0915\u0947' \u0915\u094d\u0932\u093f\u0915 \u0915\u0930\u0947 | \u0906\u092a \u0915\u094b \u091a\u0941\u0928\u0940 \u0939\u0941\u0908 \u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908 \u0926\u094b\u092c\u093e\u0930\u093e \u091a\u0932\u093e\u0928\u0940 \u0939\u094b\u0917\u0940 |", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0938\u094d\u0935\u0924\u0902\u0924\u094d\u0930 \u0938\u092e\u094d\u092a\u093e\u0926\u0928\u0915\u094d\u0937\u092e \u0915\u094d\u0937\u0947\u0924\u094d\u0930/\u0938\u094d\u0924\u092e\u094d\u092d \u092e\u0947\u0902 \u0915\u093f\u092f\u0947 \u0939\u0941\u090f \u092c\u0926\u0932 \u0905\u092d\u0940 \u0930\u0915\u094d\u0937\u093f\u0924 \u0928\u0939\u0940\u0902 \u0939\u0948\u0902 | \u0905\u0917\u0930 \u0906\u092a \u0915\u0941\u091b \u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908 \u0915\u0930\u0924\u0947 \u0939\u094b \u0924\u094b \u0935\u0947  \u0916\u094b \u091c\u093e\u092f\u0947\u0902\u0917\u0947 |"
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
    "DATE_FORMAT": "j F Y", 
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
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "m/d/Y P", 
    "SHORT_DATE_FORMAT": "d-m-Y", 
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

