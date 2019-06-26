

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
    "Changes to steps that are not selected as part of the assignment will not be saved.": "\u672a\u4f5c\u4e3a\u4f5c\u4e1a\u90e8\u5206\u7684\u6b65\u9aa4\u53d8\u66f4\u5c06\u4e0d\u4f1a\u88ab\u4fdd\u5b58\u3002", 
    "Could not retrieve download url.": "\u4e0d\u80fd\u8bfb\u53d6\u4e0b\u8f7d\u94fe\u63a5\u5730\u5740", 
    "Could not retrieve upload url.": "\u4e0d\u80fd\u8bfb\u53d6\u4e0a\u4f20\u94fe\u63a5\u5730\u5740", 
    "Couldn't Save This Assignment": "\u4fdd\u5b58\u4f5c\u4e1a\u5931\u8d25", 
    "Criterion Added": "\u6807\u51c6\u5df2\u6dfb\u52a0", 
    "Criterion Deleted": "\u89c4\u8303\u5df2\u5220\u9664", 
    "Do you want to upload your file before submitting?": "\u4f60\u786e\u5b9a\u5728\u63d0\u4ea4\u4e4b\u524d\u4e0a\u4f20\u4f60\u7684\u6587\u4ef6\u5417\uff1f", 
    "Error": "\u9519\u8bef", 
    "Error getting the number of ungraded responses": "\u83b7\u53d6\u672a\u8bc4\u5206\u56de\u590d\u6570\u91cf\u51fa\u73b0\u9519\u8bef", 
    "File type is not allowed.": "\u6587\u4ef6\u7c7b\u578b\u4e0d\u53ef\u7528\u3002", 
    "File types can not be empty.": "\u6587\u4ef6\u7c7b\u578b\u4e0d\u80fd\u4e3a\u7a7a\u3002", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "\u5982\u679c\u4f60\u4e0d\u4fdd\u5b58\u6216\u8005\u63d0\u4ea4\u7b54\u6848\u5c31\u79bb\u5f00\uff0c\u4f60\u53ef\u80fd\u4f1a\u4e22\u5931\u6389\u5199\u5b8c\u7684\u4e00\u5207\u3002", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "\u5982\u679c\u4f60\u79bb\u5f00\u672c\u9875\u65f6\u6ca1\u6709\u63d0\u4ea4\u4f60\u7684\u540c\u5b66\u4e92\u8bc4\uff0c\u4f60\u5c06\u4e22\u5931\u4f60\u6240\u505a\u7684\u4e00\u5207\u3002", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "\u5982\u679c\u4f60\u672a\u63d0\u4ea4\u4f60\u7684\u81ea\u6211\u8bc4\u4f30\u5c31\u79bb\u5f00\u6b64\u9875\u9762\uff0c\u4f60\u5c06\u4e22\u5931\u6240\u505a\u7684\u4e00\u5207\u3002", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "\u5982\u679c\u4f60\u672a\u63d0\u4ea4\u4f60\u7684\u5458\u5de5\u8bc4\u4f30\u5c31\u79bb\u5f00\u6b64\u9875\u9762\uff0c\u4f60\u5c06\u4e22\u5931\u6240\u505a\u7684\u4e00\u5207\u3002", 
    "Not Selected": "\u672a\u9009\u4e2d", 
    "One or more rescheduling tasks failed.": "\u4e00\u9879\u6216\u51e0\u9879\u6539\u671f\u4efb\u52a1\u5931\u8d25\u4e86\u3002", 
    "Option Deleted": "\u9009\u9879\u5df2\u5220\u9664", 
    "Please correct the outlined fields.": "\u8bf7\u6539\u6b63\u753b\u51fa\u533a\u57df", 
    "Saving...": "\u6b63\u5728\u4fdd\u5b58\u2026", 
    "Status of Your Response": "\u4f60\u7684\u7b54\u6848\u7684\u72b6\u6001", 
    "The display of ungraded and checked out responses could not be loaded.": "\u672a\u6253\u5206\u53ca\u5df2\u901a\u8fc7\u56de\u7b54\u7684\u7a97\u53e3\u65e0\u6cd5\u52a0\u8f7d\u3002", 
    "The following file types are not allowed: ": "\u4e0b\u5217\u6587\u4ef6\u7c7b\u578b\u4e0d\u53ef\u7528\uff1a", 
    "The server could not be contacted.": "\u65e0\u6cd5\u8054\u7cfb\u670d\u52a1\u5668\u3002", 
    "The staff assessment form could not be loaded.": "\u5de5\u4f5c\u4eba\u5458\u8bc4\u6d4b\u8868\u683c\u65e0\u6cd5\u52a0\u8f7d\u3002", 
    "The submission could not be removed from the grading pool.": "\u8be5\u63d0\u4ea4\u65e0\u6cd5\u4ece\u8bc4\u5206\u6c60\u4e2d\u5220\u9664\u3002", 
    "This assessment could not be submitted.": "\u8fd9\u4efd\u8bc4\u6d4b\u65e0\u6cd5\u63d0\u4ea4\u3002", 
    "This feedback could not be submitted.": "\u8fd9\u6761\u53cd\u9988\u65e0\u6cd5\u63d0\u4ea4\u3002", 
    "This problem could not be saved.": "\u8be5\u95ee\u9898\u65e0\u6cd5\u4fdd\u5b58\u3002", 
    "This problem has already been released. Any changes will apply only to future assessments.": "\u6b64\u95ee\u9898\u5df2\u53d1\u5e03\u3002\u4efb\u4f55\u66f4\u6539\u90fd\u53ea\u9002\u7528\u4e8e\u672a\u6765\u7684\u8bc4\u4f30\u3002", 
    "This response could not be saved.": "\u8be5\u7b54\u6848\u65e0\u6cd5\u4fdd\u5b58\u3002", 
    "This response could not be submitted.": "\u8be5\u7b54\u6848\u65e0\u6cd5\u63d0\u4ea4\u3002", 
    "This response has been saved but not submitted.": "\u8be5\u7b54\u6848\u5df2\u7ecf\u4fdd\u5b58\u4e86\uff0c\u4f46\u4ecd\u672a\u63d0\u4ea4\u3002", 
    "This response has not been saved.": "\u8be5\u7b54\u6848\u8fd8\u6ca1\u6709\u88ab\u4fdd\u5b58\u3002", 
    "This section could not be loaded.": "\u8fd9\u4e2a\u90e8\u5206\u65e0\u6cd5\u52a0\u8f7d\u3002", 
    "Unable to load": "\u4e0d\u80fd\u52a0\u8f7d", 
    "Unexpected server error.": "\u670d\u52a1\u5668\u5f02\u5e38\u9519\u8bef\u3002", 
    "Unnamed Option": "\u672a\u547d\u540d\u9009\u9879", 
    "Warning": "\u8b66\u544a", 
    "You can upload files with these file types: ": "\u4f60\u53ef\u4ee5\u4e0a\u4f20\u7684\u6587\u4ef6\u7c7b\u578b\uff1a", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "\u4f60\u5df2\u7ecf\u6dfb\u52a0\u4e86\u4e00\u4e2a\u6807\u51c6\u3002\u4f60\u5c06\u9700\u8981\u4e3a\u201c\u5b66\u5458\u8bad\u7ec3\u201d\u6b65\u9aa4\u4e2d\u7684\u6807\u51c6\u9009\u62e9\u4e00\u4e2a\u9009\u9879\u3002\u8981\u6267\u884c\u6b64\u64cd\u4f5c\uff0c\u8bf7\u5355\u51fb\u201c\u8bbe\u7f6e\u201d\u9009\u9879\u5361\u3002", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "\u4f60\u5df2\u5220\u9664\u4e86\u4e00\u4e2a\u6807\u51c6\u3002\u6b64\u6807\u51c6\u5df2\u4ece\u201c\u5b66\u5458\u8bad\u7ec3\u201d\u6b65\u9aa4\u7684\u56de\u590d\u793a\u4f8b\u4e2d\u64a4\u9500\u3002", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "\u4f60\u5df2\u5220\u9664\u6b64\u6807\u51c6\u7684\u6240\u6709\u9009\u9879\u3002\u6b64\u6807\u51c6\u5df2\u4ece\u201c\u5b66\u5458\u8bad\u7ec3\u201d\u6b65\u9aa4\u7684\u56de\u590d\u793a\u4f8b\u4e2d\u5220\u9664\u3002", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "\u4f60\u5df2\u5220\u9664\u4e00\u4e2a\u9009\u9879\u3002\u6b64\u9009\u9879\u5df2\u4ece\u201c\u5b66\u5458\u8bad\u7ec3\u201d\u6b65\u9aa4\u4e2d\u7684\u56de\u590d\u793a\u4f8b\u6807\u51c6\u4e2d\u5220\u9664\u3002\u4f60\u53ef\u80fd\u5fc5\u987b\u4e3a\u6b64\u6807\u51c6\u9009\u62e9\u4e00\u4e2a\u65b0\u9009\u9879\u3002", 
    "You must provide a learner name.": "\u4f60\u5fc5\u987b\u63d0\u4f9b\u4e00\u4e2a\u5b66\u751f\u59d3\u540d\u3002", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "\u4f60\u5c06\u4f1a\u63d0\u4ea4\u5bf9\u672c\u6b21\u4f5c\u4e1a\u7684\u7b54\u6848\u3002\u63d0\u4ea4\u540e\uff0c\u4f60\u5c06\u65e0\u6cd5\u4fee\u6539\u6216\u8005\u63d0\u4ea4\u65b0\u7684\u7b54\u6848\u3002"
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

