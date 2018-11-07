

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n==1?0:(((n%100>19)||((n%100==0)&&(n!=0)))?2:1));
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
      "%(sel)s din %(cnt)s selectate", 
      "%(sel)s din %(cnt)s selectate", 
      "de %(sel)s din %(cnt)s selectate"
    ], 
    "6 a.m.": "6 a.m.", 
    "6 p.m.": "6 p.m.", 
    "Available %s": "%s disponibil", 
    "Cancel": "Anuleaz\u0103", 
    "Choose": "Alege", 
    "Choose a Date": "Alege a dat\u0103", 
    "Choose a Time": "Alege o or\u0103", 
    "Choose a time": "Alege o or\u0103", 
    "Choose all": "Alege toate", 
    "Chosen %s": "%s alese", 
    "Click to choose all %s at once.": "Click pentru a alege toate %s.", 
    "Click to remove all chosen %s at once.": "Click pentru a elimina toate %s alese.", 
    "Filter": "Filtru", 
    "Hide": "Ascunde", 
    "Midnight": "Miezul nop\u021bii", 
    "Noon": "Amiaz\u0103", 
    "Note: You are %s hour ahead of server time.": [
      "Not\u0103: Sunte\u021bi cu %s ora \u00eenaintea orei serverului.", 
      "Not\u0103: Sunte\u021bi cu %s ore \u00eenaintea orei serverului.", 
      "Not\u0103: Sunte\u021bi cu %s ore \u00eenaintea orei serverului."
    ], 
    "Note: You are %s hour behind server time.": [
      "Not\u0103: Sunte\u021bi cu %s or\u0103 \u00een urma orei serverului.", 
      "Not\u0103: Sunte\u021bi cu %s ore \u00een urma orei serverului.", 
      "Not\u0103: Sunte\u021bi cu %s ore \u00een urma orei serverului."
    ], 
    "Now": "Acum", 
    "Remove": "Elimin\u0103", 
    "Remove all": "Elimin\u0103 toate", 
    "Show": "Arat\u0103", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Aceasta este o list\u0103 cu %s disponibile. Le pute\u021bi alege select\u00e2nd mai multe in chenarul de mai jos \u0219i ap\u0103s\u00e2nd pe s\u0103geata \"Alege\" dintre cele dou\u0103 chenare.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Aceasta este lista de %s alese. Pute\u021bi elimina din ele select\u00e2ndu-le in chenarul de mai jos \u0219i apasand pe s\u0103geata \"Elimin\u0103\" dintre cele dou\u0103 chenare.", 
    "Today": "Ast\u0103zi", 
    "Tomorrow": "M\u00e2ine", 
    "Type into this box to filter down the list of available %s.": "Scrie \u00een acest chenar pentru a filtra lista de %s disponibile.", 
    "Yesterday": "Ieri", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "A\u021bi selectat o ac\u0163iune \u0219i nu a\u021b\u0163i f\u0103cut modific\u0103ri \u00een c\u00eempuri individuale. Probabil c\u0103uta\u021bi butonul Go, \u00een loc de Salveaz\u0103.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "A\u0163i selectat o ac\u0163iune, dar nu a\u0163i salvat \u00eenc\u0103 modific\u0103rile la c\u00e2mpuri individuale. Face\u0163i clic pe OK pentru a salva. Va trebui s\u0103 executa\u021bi ac\u021biunea din nou.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Ave\u0163i modific\u0103ri nesalvate \u00een c\u00eempuri individuale editabile. Dac\u0103 executa\u0163i o ac\u021biune, modific\u0103rile nesalvate vor fi pierdute."
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
    "DATETIME_FORMAT": "j F Y, H:i", 
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
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "d.m.Y, H:i", 
    "SHORT_DATE_FORMAT": "d.m.Y", 
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

