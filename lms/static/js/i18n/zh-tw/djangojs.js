

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
    "Changes to steps that are not selected as part of the assignment will not be saved.": "\u60a8\u5df2\u53d6\u6d88\u9078\u64c7\u6b64\u8a55\u5206\u6b65\u9a5f\uff0c\u9019\u5c07\u4f7f\u5b83\u4e0d\u6703\u88ab\u5132\u5b58\u3002", 
    "Could not retrieve download url.": "\u7121\u6cd5\u627e\u5230\u4e0b\u8f09\u7db2\u5740", 
    "Could not retrieve upload url.": "\u7121\u6cd5\u627e\u5230\u4e0a\u50b3\u7db2\u5740", 
    "Couldn't Save This Assignment": "\u4e0d\u80fd\u5132\u5b58\u9019\u4f5c\u696d", 
    "Criterion Added": " \u589e\u52a0\u8a55\u5206\u6a19\u6e96", 
    "Criterion Deleted": "\u522a\u9664\u8a55\u5206\u6a19\u6e96", 
    "Do you want to upload your file before submitting?": "\u4f60\u60f3\u5728\u63d0\u4ea4\u524d\u4e0a\u50b3\u60a8\u7684\u6a94\u6848\uff1f", 
    "Error": "\u932f\u8aa4", 
    "Error getting the number of ungraded responses": "\u932f\u8aa4\u7372\u53d6\u4e0d\u5206\u7d1a\u7684\u56de\u61c9\u6578\u3002", 
    "File type is not allowed.": "\u6a94\u6848\u985e\u578b\u662f\u4e0d\u5141\u8a31\u7684\u3002", 
    "File types can not be empty.": "\u6a94\u6848\u985e\u578b\u4e0d\u53ef\u7a7a\u767d\u3002", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "\u5982\u679c\u4f60\u6c92\u6709\u5132\u5b58\u6216\u63d0\u4ea4\u4f60\u7684\u4f5c\u7b54\u800c\u96e2\u958b\u9019\u500b\u9801\u9762\uff0c\u4f60\u5c07\u907a\u5931\u4f60\u4efb\u4f55\u5df2\u4f5c\u7b54\u7684\u4f5c\u696d\u3002", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "\u5982\u679c\u4f60\u6c92\u6709\u63d0\u4ea4\u540c\u5115\u4e92\u8a55\u800c\u96e2\u958b\u9019\u500b\u9801\u9762\uff0c\u4f60\u5c07\u907a\u5931\u4efb\u4f55\u9019\u90e8\u5206\u7684\u4f5c\u696d\u3002", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "\u5982\u679c\u4f60\u6c92\u6709\u63d0\u4ea4\u4f60\u7684\u81ea\u8a55\u800c\u96e2\u958b\u9019\u500b\u9801\u9762\uff0c\u4f60\u5c07\u907a\u5931\u4f60\u4efb\u4f55\u4f60\u6240\u505a\u7684\u4f5c\u696d\u3002", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "\u5982\u679c\u4f60\u6c92\u6709\u63d0\u4ea4\u5de5\u4f5c\u4eba\u54e1\u8a55\u4f30\u800c\u96e2\u958b\u9019\u500b\u9801\u9762\uff0c\u4f60\u5c07\u6703\u907a\u5931\u4efb\u4f55\u4f60\u6240\u505a\u7684\u4f5c\u696d\u3002", 
    "Not Selected": "\u672a\u9078\u53d6", 
    "One or more rescheduling tasks failed.": "\u4e00\u500b\u6216\u591a\u500b\u4efb\u52d9\u91cd\u65b0\u5b89\u6392\u5931\u6557\u3002", 
    "Option Deleted": "\u522a\u9664\u9078\u9805", 
    "Please correct the outlined fields.": "\u8acb\u66f4\u6b63\u7cfb\u7d71\u986f\u793a\u7684\u6b04\u4f4d\u3002", 
    "Saving...": "\u5132\u5b58\u4e2d", 
    "Status of Your Response": "\u60a8\u7684\u4f5c\u7b54\u4e4b\u72c0\u614b", 
    "The display of ungraded and checked out responses could not be loaded.": "\u4e0d\u5206\u7d1a\u8207\u5df2\u56de\u61c9\u7684\u986f\u793a\u7121\u6cd5\u8f09\u5165\u3002", 
    "The following file types are not allowed: ": "\u4e0b\u5217\u6a94\u6848\u985e\u578b\u662f\u4e0d\u5141\u8a31\u7684\uff1a", 
    "The server could not be contacted.": "\u7121\u6cd5\u806f\u7e6b\u670d\u52d9\u5668\u3002", 
    "The staff assessment form could not be loaded.": "\u5de5\u4f5c\u4eba\u54e1\u8a55\u5206\u8868\u7121\u6cd5\u8f09\u5165\u3002", 
    "The submission could not be removed from the grading pool.": "\u6b64\u63d0\u4ea4\u4e0d\u80fd\u5f9e\u8a55\u5206\u5eab\u4e2d\u79fb\u9664\u3002", 
    "This assessment could not be submitted.": "\u9019\u4efd\u8a55\u5206\u7121\u6cd5\u63d0\u4ea4\u3002", 
    "This feedback could not be submitted.": "\u9019\u689d\u53cd\u994b\u610f\u898b\u7121\u6cd5\u63d0\u4ea4\u3002", 
    "This problem could not be saved.": "\u6b64\u554f\u984c\u7121\u6cd5\u5132\u5b58\u3002", 
    "This problem has already been released. Any changes will apply only to future assessments.": "\u6b64\u554f\u984c\u5df2\u7d93\u88ab\u91cb\u51fa\u4e86\u3002\u4efb\u4f55\u66f4\u6539\u90fd\u53ea\u6703\u5728\u672a\u4f86\u7684\u8a55\u5206\u4e2d\u51fa\u73fe\u3002", 
    "This response could not be saved.": "\u4f5c\u7b54\u7121\u6cd5\u4fdd\u5b58\u3002", 
    "This response could not be submitted.": "\u4f5c\u7b54\u7121\u6cd5\u63d0\u4ea4\u3002", 
    "This response has been saved but not submitted.": "\u9019\u4e00\u4efd\u4f5c\u7b54\u5df2\u7d93\u5132\u5b58\u4e86\uff0c\u4f46\u4ecd\u672a\u63d0\u4ea4\u3002", 
    "This response has not been saved.": "\u4f5c\u7b54\u5c1a\u672a\u5132\u5b58\u3002", 
    "This section could not be loaded.": "\u9019\u500b\u90e8\u5206\u7121\u6cd5\u52a0\u8f09\u3002", 
    "Unable to load": "\u7121\u6cd5\u8f09\u5165", 
    "Unexpected server error.": "\u672a\u9810\u671f\u7684\u4f3a\u670d\u5668\u932f\u8aa4", 
    "Unnamed Option": "\u672a\u547d\u540d\u7684\u9078\u9805", 
    "Warning": "\u8b66\u544a", 
    "You can upload files with these file types: ": "\u60a8\u53ef\u4ee5\u4e0a\u50b3\u9019\u4e9b\u985e\u578b\u7684\u6a94\u6848\uff1a", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "\u60a8\u5fc5\u9808\u589e\u52a0\u8a55\u5206\u6a19\u6e96\u3002\u60a8\u5c07\u6703\u9700\u8981\u5728\u8a55\u5206\u7df4\u7fd2\u6b65\u9a5f\u4e2d\u9078\u64c7\u8a55\u5206\u6a19\u6e96\u9078\u9805\u3002\u8acb\u9ede\u9078\u8a2d\u5b9a\u6a19\u8b58\u4ee5\u5b8c\u6210\u6b64\u6b65\u9a5f\u3002", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "\u60a8\u5df2\u7d93\u522a\u9664 \u4e00\u500b\u6a19\u6e96\u3002\u5728\u8a55\u5206\u7df4\u7fd2\u4e2d\uff0c\u8a72\u6a19\u6e96\u5df2\u7d93\u5f9e\u7bc4\u4f8b\u4f5c\u7b54\u88e1\u522a\u9664\u3002", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "\u60a8\u5df2\u7d93\u522a\u9664\u4e86\u9019\u8a55\u5206\u6a19\u6e96\u4e2d\u6240\u6709\u7684\u9078\u9805\uff0c\u5df2\u7d93\u5f9e\u7bc4\u4f8b\u4f5c\u7b54\u88e1\u522a\u9664\u8a55\u5206\u6a19\u6e96\u3002", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "\u60a8\u5df2\u7d93\u522a\u9664 \u4e00\u500b\u9078\u9805\u3002\u5728\u8a55\u5206\u7df4\u7fd2\u6b65\u9a5f\u4e2d\uff0c\u7cfb\u7d71\u5df2\u7d93\u5f9e\u7bc4\u4f8b\u4f5c\u7b54\u88e1\u522a\u9664\u8a55\u5206\u6a19\u6e96\u4e2d\u7684\u9078\u9805\u3002\u60a8\u5fc5\u9808\u70ba\u9019\u8a55\u5206\u6a19\u6e96\u9078\u64c7\u65b0\u7684\u9078\u9805\u3002", 
    "You must provide a learner name.": "\u4f60\u5fc5\u9808\u63d0\u4f9b\u4e00\u500b\u5b78\u7fd2\u8005\u5168\u540d", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "\u60a8\u5373\u5c07\u9001\u51fa\u4f60\u7684\u4f5c\u7b54\uff0c\u4e00\u65e6\u9001\u51fa\u4f5c\u7b54\u5c31\u4e0d\u80fd\u4fee\u6539\uff0c\u4e5f\u7121\u6cd5\u91cd\u65b0\u9001\u51fa\u65b0\u7684\u4f5c\u7b54\u3002"
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
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "F j", 
    "NUMBER_GROUPING": "0", 
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

