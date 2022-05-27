

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
      "\u0538\u0576\u057f\u0580\u057e\u0561\u056e \u0567 %(cnt)s-\u056b\u0581 %(sel)s-\u0568",
      "\u0538\u0576\u057f\u0580\u057e\u0561\u056e \u0567 %(cnt)s-\u056b\u0581 %(sel)s-\u0568"
    ],
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "April": "\u0531\u057a\u0580\u056b\u056c",
    "August": "\u0555\u0563\u0578\u057d\u057f\u0578\u057d",
    "Available %s": "\u0540\u0561\u057d\u0561\u0576\u0565\u056c\u056b %s",
    "Cancel": "\u0549\u0565\u0572\u0561\u0580\u056f\u0565\u056c",
    "Choose": "\u0538\u0576\u057f\u0580\u0565\u056c",
    "Choose a Date": "\u0538\u0576\u057f\u0580\u0565\u0584 \u0561\u0574\u057d\u0561\u0569\u056b\u057e",
    "Choose a Time": "\u0538\u0576\u057f\u0580\u0565\u0584 \u056a\u0561\u0574\u0561\u0576\u0561\u056f",
    "Choose a time": "\u0538\u0576\u057f\u0580\u0565\u0584 \u056a\u0561\u0574\u0561\u0576\u0561\u056f",
    "Choose all": "\u0538\u0576\u057f\u0580\u0565\u056c \u0562\u0578\u056c\u0578\u0580\u0568",
    "Chosen %s": "\u0538\u0576\u057f\u0580\u057e\u0561\u056e %s",
    "Click to choose all %s at once.": "\u054d\u0565\u0572\u0574\u0565\u0584 \u0562\u0578\u056c\u0578\u0580 %s\u0568 \u0568\u0576\u057f\u0580\u0565\u056c\u0578\u0582 \u0570\u0561\u0574\u0561\u0580\u0589",
    "Click to remove all chosen %s at once.": "\u054d\u0565\u0572\u0574\u0565\u0584 \u0562\u0578\u056c\u0578\u0580 %s\u0568 \u0570\u0565\u057c\u0561\u0581\u0576\u0565\u056c\u0578\u0582 \u0570\u0561\u0574\u0561\u0580\u0589",
    "December": "\u0534\u0565\u056f\u057f\u0565\u0574\u0562\u0565\u0580",
    "February": "\u0553\u0565\u057f\u0580\u057e\u0561\u0580",
    "Filter": "\u0556\u056b\u056c\u057f\u0580\u0565\u056c",
    "Hide": "\u0539\u0561\u0584\u0581\u0576\u0565\u056c",
    "January": "\u0540\u0578\u0582\u0576\u057e\u0561\u0580",
    "July": "\u0540\u0578\u0582\u056c\u056b\u057d",
    "June": "\u0540\u0578\u0582\u0576\u056b\u057d",
    "March": "\u0544\u0561\u0580\u057f",
    "May": "\u0544\u0561\u0575\u056b\u057d",
    "Midnight": "\u053f\u0565\u057d\u0563\u056b\u0577\u0565\u0580",
    "Noon": "\u053f\u0565\u057d\u0585\u0580",
    "Note: You are %s hour ahead of server time.": [
      "\u0541\u0565\u0580 \u056a\u0561\u0574\u0568 \u0561\u057c\u0561\u057b \u0567 \u057d\u0565\u0580\u057e\u0565\u0580\u056b \u056a\u0561\u0574\u0561\u0576\u0561\u056f\u056b\u0581 %s \u056a\u0561\u0574\u0578\u057e",
      "\u0541\u0565\u0580 \u056a\u0561\u0574\u0568 \u0561\u057c\u0561\u057b \u0567 \u057d\u0565\u0580\u057e\u0565\u0580\u056b \u056a\u0561\u0574\u0561\u0576\u0561\u056f\u056b\u0581 %s \u056a\u0561\u0574\u0578\u057e"
    ],
    "Note: You are %s hour behind server time.": [
      "\u0541\u0565\u0580 \u056a\u0561\u0574\u0568 \u0570\u0565\u057f \u0567 \u057d\u0565\u0580\u057e\u0565\u0580\u056b \u056a\u0561\u0574\u0561\u0576\u0561\u056f\u056b\u0581 %s \u056a\u0561\u0574\u0578\u057e",
      "\u0541\u0565\u0580 \u056a\u0561\u0574\u0568 \u0570\u0565\u057f \u0567 \u057d\u0565\u0580\u057e\u0565\u0580\u056b \u056a\u0561\u0574\u0561\u0576\u0561\u056f\u056b\u0581 %s \u056a\u0561\u0574\u0578\u057e"
    ],
    "November": "\u0546\u0578\u0575\u0565\u0574\u0562\u0565\u0580",
    "Now": "\u0540\u056b\u0574\u0561",
    "October": "\u0540\u0578\u056f\u057f\u0565\u0574\u0562\u0565\u0580",
    "Remove": "\u0540\u0565\u057c\u0561\u0581\u0576\u0565\u056c",
    "Remove all": "\u0540\u0565\u057c\u0561\u0581\u0576\u0565\u056c \u0562\u0578\u056c\u0578\u0580\u0568",
    "September": "\u054d\u0565\u057a\u057f\u0565\u0574\u0562\u0565\u0580",
    "Show": "\u0551\u0578\u0582\u0575\u0581 \u057f\u0561\u056c",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u054d\u0561 \u0570\u0561\u057d\u0561\u0576\u0565\u056c\u056b %s \u0581\u0578\u0582\u0581\u0561\u056f \u0567\u0589 \u0534\u0578\u0582\u0584 \u056f\u0561\u0580\u0578\u0572 \u0565\u0584 \u0568\u0576\u057f\u0580\u0565\u056c \u0576\u0580\u0561\u0576\u0581\u056b\u0581 \u0578\u0580\u0578\u0577\u0576\u0565\u0580\u0568 \u0568\u0576\u057f\u0580\u0565\u056c\u0578\u057e \u0564\u0580\u0561\u0576\u0584 \u057d\u057f\u0578\u0580\u0587 \u0563\u057f\u0576\u057e\u0578\u0572 \u057e\u0561\u0576\u0564\u0561\u056f\u0578\u0582\u0574 \u0587 \u057d\u0565\u0572\u0574\u0565\u056c\u0578\u057e \u0565\u0580\u056f\u0578\u0582 \u057e\u0561\u0576\u0564\u0561\u056f\u0576\u0565\u0580\u056b \u0574\u056b\u057b\u0587 \u0563\u057f\u0576\u057e\u0578\u0572 \"\u0538\u0576\u057f\u0580\u0565\u056c\" \u057d\u056c\u0561\u0584\u0568\u0589",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u054d\u0561 \u0570\u0561\u057d\u0561\u0576\u0565\u056c\u056b %s\u056b \u0581\u0578\u0582\u0581\u0561\u056f \u0567\u0589 \u0534\u0578\u0582\u0584 \u056f\u0561\u0580\u0578\u0572 \u0565\u0584 \u0570\u0565\u057c\u0561\u0581\u0576\u0565\u056c \u0576\u0580\u0561\u0576\u0581\u056b\u0581 \u0578\u0580\u0578\u0577\u0576\u0565\u0580\u0568 \u0568\u0576\u057f\u0580\u0565\u056c\u0578\u057e \u0564\u0580\u0561\u0576\u0584 \u057d\u057f\u0578\u0580\u0587 \u0563\u057f\u0576\u057e\u0578\u0572 \u057e\u0561\u0576\u0564\u0561\u056f\u0578\u0582\u0574 \u0587 \u057d\u0565\u0572\u0574\u0565\u056c\u0578\u057e \u0565\u0580\u056f\u0578\u0582 \u057e\u0561\u0576\u0564\u0561\u056f\u0576\u0565\u0580\u056b \u0574\u056b\u057b\u0587 \u0563\u057f\u0576\u057e\u0578\u0572 \"\u0540\u0565\u057c\u0561\u0581\u0576\u0565\u056c\" \u057d\u056c\u0561\u0584\u0568\u0589",
    "Today": "\u0531\u0575\u057d\u0585\u0580",
    "Tomorrow": "\u054e\u0561\u0572\u0568",
    "Type into this box to filter down the list of available %s.": "\u0544\u0578\u0582\u057f\u0584\u0561\u0563\u0580\u0565\u0584 \u0561\u0575\u057d \u0564\u0561\u0577\u057f\u0578\u0582\u0574 \u0570\u0561\u057d\u0561\u0576\u0565\u056c\u056b %s \u0581\u0578\u0582\u0581\u0561\u056f\u0568 \u0586\u056b\u056c\u057f\u0580\u0565\u056c\u0578\u0582 \u0570\u0561\u0574\u0561\u0580\u0589",
    "Yesterday": "\u0535\u0580\u0565\u056f",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0534\u0578\u0582\u0584 \u0568\u0576\u057f\u0580\u0565\u056c \u0565\u0584 \u0563\u0578\u0580\u056e\u0578\u0572\u0578\u0582\u0569\u0575\u0578\u0582\u0576, \u0562\u0561\u0575\u0581 \u0564\u0565\u057c \u0579\u0565\u0584 \u056f\u0561\u057f\u0561\u0580\u0565\u056c \u0578\u0580\u0587\u0567 \u0561\u0576\u0570\u0561\u057f\u0561\u056f\u0561\u0576 \u056d\u0574\u0562\u0561\u0563\u0580\u0565\u056c\u056b \u0564\u0561\u0577\u057f\u0565\u0580\u056b \u0583\u0578\u0583\u0578\u056d\u0578\u0582\u0569\u0575\u0578\u0582\u0576 \u0541\u0565\u0566 \u0570\u0561\u057e\u0561\u0576\u0561\u0562\u0561\u0580 \u057a\u0565\u057f\u0584 \u0567 \u053f\u0561\u057f\u0561\u0580\u0565\u056c \u056f\u0578\u0573\u0561\u056f\u0568, \u054a\u0561\u0570\u057a\u0561\u0576\u0565\u056c \u056f\u0578\u0573\u0561\u056f\u056b \u0583\u0578\u056d\u0561\u0580\u0565\u0576",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0534\u0578\u0582\u0584 \u0568\u0576\u057f\u0580\u0565\u056c \u0565\u0584 \u0563\u0578\u0580\u056e\u0578\u0572\u0578\u0582\u0569\u0575\u0578\u0582\u0576, \u0562\u0561\u0575\u0581 \u0564\u0565\u057c \u0579\u0565\u0584 \u057a\u0561\u0570\u057a\u0561\u0576\u0565\u056c \u0561\u0576\u0570\u0561\u057f\u0561\u056f\u0561\u0576 \u056d\u0574\u0562\u0561\u0563\u0580\u0565\u056c\u056b \u0564\u0561\u0577\u057f\u0565\u0580\u056b \u0583\u0578\u0583\u0578\u056d\u0578\u0582\u0569\u0575\u0578\u0582\u0576\u0576\u0565\u0580\u0568 \u054d\u0565\u0572\u0574\u0565\u0584 OK \u057a\u0561\u0570\u057a\u0561\u0576\u0565\u056c\u0578\u0582 \u0570\u0561\u0574\u0561\u0580\u0589 \u0531\u0576\u0570\u0580\u0561\u056a\u0565\u0577\u057f \u056f\u056c\u056b\u0576\u056b \u057e\u0565\u0580\u0561\u0563\u0578\u0580\u056e\u0561\u0580\u056f\u0565\u056c \u0563\u0578\u0580\u056e\u0578\u0572\u0578\u0582\u0569\u0575\u0578\u0582\u0576\u0568",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0534\u0578\u0582\u0584 \u0578\u0582\u0576\u0565\u0584 \u0579\u057a\u0561\u0570\u057a\u0561\u0576\u057e\u0561\u056e \u0561\u0576\u0570\u0561\u057f\u0561\u056f\u0561\u0576 \u056d\u0574\u0562\u0561\u0563\u0580\u0565\u056c\u056b \u0564\u0561\u0577\u057f\u0565\u0580\u0589 \u0535\u0569\u0565 \u0564\u0578\u0582\u0584 \u056f\u0561\u057f\u0561\u0580\u0565\u0584 \u0563\u0578\u0580\u056e\u0578\u0572\u0578\u0582\u0569\u0575\u0578\u0582\u0576\u0568, \u0571\u0565\u0580 \u0579\u057a\u0561\u0570\u057a\u0561\u0576\u057e\u0561\u056e \u0583\u0578\u0583\u0578\u056d\u0578\u0582\u0569\u0575\u0578\u0582\u0576\u0576\u0565\u0580\u0568 \u056f\u056f\u0578\u0580\u0565\u0576\u0589",
    "one letter Friday\u0004F": "\u0548\u0552",
    "one letter Monday\u0004M": "\u0535",
    "one letter Saturday\u0004S": "\u0547",
    "one letter Sunday\u0004S": "\u053f",
    "one letter Thursday\u0004T": "\u0540",
    "one letter Tuesday\u0004T": "\u0535",
    "one letter Wednesday\u0004W": "\u0549"
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

