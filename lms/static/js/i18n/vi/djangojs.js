

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=0;
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
      " %(sel)s  c\u1ee7a %(cnt)s \u0111\u01b0\u1ee3c ch\u1ecdn"
    ], 
    "6 a.m.": "6 gi\u1edd s\u00e1ng", 
    "Available %s": "C\u00f3 s\u1eb5n %s", 
    "Cancel": "H\u1ee7y b\u1ecf", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Nh\u1eefng thay \u0111\u1ed5i \u1edf c\u00e1c b\u01b0\u1edbc kh\u00f4ng \u0111\u01b0\u1ee3c ch\u1ecdn thu\u1ed9c m\u1ed9t ph\u1ea7n c\u1ee7a b\u00e0i t\u1eadp s\u1ebd kh\u00f4ng \u0111\u01b0\u1ee3c l\u01b0u.", 
    "Choose": "Ch\u1ecdn", 
    "Choose a time": "Ch\u1ecdn gi\u1edd", 
    "Choose all": "Ch\u1ecdn t\u1ea5t c\u1ea3", 
    "Chosen %s": "Ch\u1ecdn %s", 
    "Click to choose all %s at once.": "Click \u0111\u1ec3 ch\u1ecdn t\u1ea5t c\u1ea3 %s .", 
    "Click to remove all chosen %s at once.": "Click \u0111\u1ec3 b\u1ecf ch\u1ecdn t\u1ea5t c\u1ea3 %s", 
    "Could not retrieve download url.": "Kh\u00f4ng th\u1ec3 t\u00ecm th\u1ea5y \u0111\u01b0\u1eddng d\u1eabn t\u1ea3i xu\u1ed1ng.", 
    "Could not retrieve upload url.": "Kh\u00f4ng th\u1ec3 t\u00ecm th\u1ea5y \u0111\u01b0\u1eddng d\u1eabn t\u1ea3i l\u00ean.", 
    "Couldn't Save This Assignment": "Kh\u00f4ng Th\u1ec3 L\u01b0u B\u00e0i T\u1eadp N\u00e0y", 
    "Error": "L\u1ed7i", 
    "Filter": "L\u1ecdc", 
    "Hide": "D\u1ea5u \u0111i", 
    "Midnight": "N\u1eeda \u0111\u00eam", 
    "Noon": "Bu\u1ed5i tr\u01b0a", 
    "Not Selected": "Kh\u00f4ng \u0110\u01b0\u1ee3c Ch\u1ecdn", 
    "Note: You are %s hour ahead of server time.": [
      "L\u01b0u \u00fd: Hi\u1ec7n t\u1ea1i b\u1ea1n \u0111ang th\u1ea5y th\u1eddi gian tr\u01b0\u1edbc %s gi\u1edd so v\u1edbi th\u1eddi gian m\u00e1y ch\u1ee7."
    ], 
    "Note: You are %s hour behind server time.": [
      "L\u01b0u \u00fd: Hi\u1ec7n t\u1ea1i b\u1ea1n \u0111ang th\u1ea5y th\u1eddi gian sau %s gi\u1edd so v\u1edbi th\u1eddi gian m\u00e1y ch\u1ee7."
    ], 
    "Now": "B\u00e2y gi\u1edd", 
    "One or more rescheduling tasks failed.": "M\u1ed9t ho\u1eb7c nhi\u1ec1u t\u00e1c v\u1ee5 \u0111i\u1ec1u ch\u1ec9nh l\u1ecbch h\u1ecdc \u0111\u00e3 th\u1ea5t b\u1ea1i.", 
    "Option Deleted": "\u0110\u00e3 X\u00f3a T\u00f9y Ch\u1ecdn", 
    "Remove": "X\u00f3a", 
    "Remove all": "Xo\u00e1 t\u1ea5t c\u1ea3", 
    "Saving...": "\u0110ang l\u01b0u...", 
    "Show": "Hi\u1ec7n ra", 
    "Status of Your Response": "Tr\u1ea1ng Th\u00e1i Tr\u1ea3 L\u1eddi C\u1ee7a B\u1ea1n", 
    "The server could not be contacted.": "Kh\u00f4ng th\u1ec3 li\u00ean h\u1ec7 v\u1edbi m\u00e1y ch\u1ee7.", 
    "The submission could not be removed from the grading pool.": "B\u00e0i n\u1ed9p kh\u00f4ng th\u1ec3 g\u1ee1 b\u1ecf kh\u1ecfi h\u1ec7 th\u1ed1ng ch\u1ea5m \u0111i\u1ec3m.", 
    "This assessment could not be submitted.": "Kh\u00f4ng th\u1ec3 g\u1eedi \u0111\u00e1nh gi\u00e1 n\u00e0y.", 
    "This feedback could not be submitted.": "Kh\u00f4ng th\u1ec3 g\u1eedi ph\u1ea3n h\u1ed3i n\u00e0y.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Danh s\u00e1ch c\u00e1c l\u1ef1a ch\u1ecdn \u0111ang c\u00f3 %s. B\u1ea1n c\u00f3 th\u1ec3 ch\u1ecdn b\u1eb1ng b\u00e1ch click v\u00e0o m\u0169i t\u00ean \"Ch\u1ecdn\" n\u1eb1m gi\u1eefa hai h\u1ed9p.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Danh s\u00e1ch b\u1ea1n \u0111\u00e3 ch\u1ecdn %s. B\u1ea1n c\u00f3 th\u1ec3 b\u1ecf ch\u1ecdn b\u1eb1ng c\u00e1ch click v\u00e0o m\u0169i t\u00ean \"Xo\u00e1\" n\u1eb1m gi\u1eefa hai \u00f4.", 
    "This problem could not be saved.": "Kh\u00f4ng th\u1ec3 l\u01b0u c\u00e2u h\u1ecfi n\u00e0y.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "C\u00e2u h\u1ecfi n\u00e0y \u0111\u00e3 \u0111\u01b0\u1ee3c \u0111\u0103ng. B\u1ea5t k\u1ef3 thay \u0111\u1ed5i n\u00e0o c\u0169ng ch\u1ec9 \u1ea3nh h\u01b0\u1edfng \u0111\u1ebfn nh\u1eefng \u0111\u00e1nh gi\u00e1 trong t\u01b0\u01a1ng lai.", 
    "This response could not be saved.": "Kh\u00f4ng th\u1ec3 l\u01b0u c\u00e2u tr\u1ea3 l\u1eddi n\u00e0y.", 
    "This response could not be submitted.": "Kh\u00f4ng th\u1ec3 g\u1eedi c\u00e2u tr\u1ea3 l\u1eddi n\u00e0y.", 
    "This response has been saved but not submitted.": "C\u00e2u tr\u1ea3 l\u1eddi n\u00e0y \u0111\u00e3 \u0111\u01b0\u1ee3c l\u01b0u nh\u01b0ng ch\u01b0a \u0111\u01b0\u1ee3c g\u1eedi \u0111i.", 
    "This response has not been saved.": "C\u00e2u tr\u1ea3 l\u1eddi n\u00e0y ch\u01b0a \u0111\u01b0\u1ee3c l\u01b0u.", 
    "This section could not be loaded.": "Kh\u00f4ng th\u1ec3 t\u1ea3i m\u1ee5c n\u00e0y.", 
    "Today": "H\u00f4m nay", 
    "Tomorrow": "Ng\u00e0y mai", 
    "Type into this box to filter down the list of available %s.": "B\u1ea1n h\u00e3y nh\u1eadp v\u00e0o \u00f4 n\u00e0y \u0111\u1ec3 l\u1ecdc c\u00e1c danh s\u00e1ch sau %s.", 
    "Unnamed Option": "T\u00f9y Ch\u1ecdn Ch\u01b0a \u0110\u1eb7t T\u00ean", 
    "Warning": "C\u1ea3nh b\u00e1o", 
    "Yesterday": "H\u00f4m qua", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "B\u1ea1n \u0111\u00e3 l\u1ef1a ch\u1ecdn m\u1ed9t h\u00e0nh \u0111\u1ed9ng, v\u00e0 b\u1ea1n \u0111\u00e3 kh\u00f4ng th\u1ef1c hi\u1ec7n b\u1ea5t k\u1ef3 thay \u0111\u1ed5i n\u00e0o tr\u00ean c\u00e1c tr\u01b0\u1eddng. C\u00f3 l\u1ebd b\u1ea1n \u0111ang t\u00ecm ki\u1ebfm n\u00fat b\u1ea5m Go thay v\u00ec n\u00fat b\u1ea5m Save.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "B\u1ea1n \u0111\u00e3 l\u1ef1a ch\u1ecdn m\u1ed9t h\u00e0nh \u0111\u1ed9ng, nh\u01b0ng b\u1ea1n kh\u00f4ng l\u01b0u thay \u0111\u1ed5i c\u1ee7a b\u1ea1n \u0111\u1ebfn c\u00e1c l\u0129nh v\u1ef1c c\u00e1 nh\u00e2n \u0111\u01b0\u1ee3c n\u00eau ra. Xin vui l\u00f2ng click OK \u0111\u1ec3 l\u01b0u l\u1ea1i. B\u1ea1n s\u1ebd c\u1ea7n ph\u1ea3i ch\u1ea1y l\u1ea1i c\u00e1c h\u00e0nh \u0111\u1ed9ng.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "B\u1ea1n ch\u01b0a l\u01b0u nh\u1eefng tr\u01b0\u1eddng \u0111\u00e3 ch\u1ec9nh s\u1eeda. N\u1ebfu b\u1ea1n ch\u1ecdn h\u00e0nh \u0111\u1ed9ng n\u00e0y, nh\u1eefng ch\u1ec9nh s\u1eeda ch\u01b0a \u0111\u01b0\u1ee3c l\u01b0u s\u1ebd b\u1ecb m\u1ea5t.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "B\u1ea1n s\u1eafp n\u1ed9p c\u00e2u tr\u1ea3 l\u1eddi cho b\u00e0i t\u1eadp n\u00e0y. Sau khi g\u1eedi b\u00e0i b\u1ea1n s\u1ebd kh\u00f4ng th\u1ec3 ch\u1ec9nh s\u1eeda ho\u1eb7c n\u1ed9p b\u00e0i m\u1edbi. "
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
    "DATETIME_FORMAT": "H:i \\N\\g\u00e0\\y d \\t\\h\u00e1\\n\\g n \\n\u0103\\m Y", 
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
    "DATE_FORMAT": "\\N\\g\u00e0\\y d \\t\\h\u00e1\\n\\g n \\n\u0103\\m Y", 
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
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "H:i d-m-Y", 
    "SHORT_DATE_FORMAT": "d-m-Y", 
    "THOUSAND_SEPARATOR": ".", 
    "TIME_FORMAT": "H:i", 
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

