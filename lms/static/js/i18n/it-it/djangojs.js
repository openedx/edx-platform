

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
      "%(sel)s di %(cnt)s selezionato", 
      "%(sel)s di %(cnt)s selezionati"
    ], 
    "6 a.m.": "6 del mattino", 
    "6 p.m.": "6 del pomeriggio", 
    "April": "Aprile", 
    "August": "Agosto", 
    "Available %s": "%s disponibili", 
    "Cancel": "Annulla", 
    "Choose": "Scegli", 
    "Choose a Date": "Scegli una data", 
    "Choose a Time": "Scegli un orario", 
    "Choose a time": "Scegli un orario", 
    "Choose all": "Scegli tutto", 
    "Chosen %s": "%s scelti", 
    "Click to choose all %s at once.": "Fai clic per scegliere tutti i %s in una volta.", 
    "Click to remove all chosen %s at once.": "Fai clic per eliminare tutti i %s in una volta.", 
    "December": "Dicembre", 
    "February": "Febbraio", 
    "Filter": "Filtro", 
    "Hide": "Nascondi", 
    "January": "Gennaio", 
    "July": "Luglio", 
    "June": "Giugno", 
    "March": "Marzo", 
    "May": "Maggio", 
    "Midnight": "Mezzanotte", 
    "Noon": "Mezzogiorno", 
    "Note: You are %s hour ahead of server time.": [
      "Nota: Sei %s ora in anticipo rispetto al server.", 
      "Nota: Sei %s ore in anticipo rispetto al server."
    ], 
    "Note: You are %s hour behind server time.": [
      "Nota: Sei %s ora in ritardo rispetto al server.", 
      "Nota: Sei %s ore in ritardo rispetto al server."
    ], 
    "November": "Novembre", 
    "Now": "Adesso", 
    "October": "Ottobre", 
    "Remove": "Elimina", 
    "Remove all": "Elimina tutti", 
    "September": "Settembre", 
    "Show": "Mostra", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Questa \u00e8 la lista dei %s disponibili. Puoi sceglierne alcuni selezionandoli nella casella qui sotto e poi facendo clic sulla freccia \"Scegli\" tra le due caselle.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Questa \u00e8 la lista dei %s scelti. Puoi eliminarne alcuni selezionandoli nella casella qui sotto e poi facendo clic sulla freccia \"Elimina\" tra le due caselle.", 
    "Today": "Oggi", 
    "Tomorrow": "Domani", 
    "Type into this box to filter down the list of available %s.": "Scrivi in questa casella per filtrare l'elenco dei %s disponibili.", 
    "Yesterday": "Ieri", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Hai selezionato un'azione, e non hai ancora apportato alcuna modifica a campi singoli. Probabilmente stai cercando il pulsante Go, invece di Save.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Hai selezionato un'azione, ma non hai ancora salvato le modifiche apportate a campi singoli. Fai clic su OK per salvare. Poi dovrai ri-eseguire l'azione.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Ci sono aggiornamenti non salvati su singoli campi modificabili. Se esegui un'azione, le modifiche non salvate andranno perse.", 
    "one letter Friday\u0004F": "V", 
    "one letter Monday\u0004M": "L", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "D", 
    "one letter Thursday\u0004T": "G", 
    "one letter Tuesday\u0004T": "Ma", 
    "one letter Wednesday\u0004W": "Me"
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
    "DATETIME_FORMAT": "l d F Y H:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S", 
      "%d/%m/%Y %H:%M:%S.%f", 
      "%d/%m/%Y %H:%M", 
      "%d/%m/%Y", 
      "%d/%m/%y %H:%M:%S", 
      "%d/%m/%y %H:%M:%S.%f", 
      "%d/%m/%y %H:%M", 
      "%d/%m/%y", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d", 
      "%d-%m-%Y %H:%M:%S", 
      "%d-%m-%Y %H:%M:%S.%f", 
      "%d-%m-%Y %H:%M", 
      "%d-%m-%Y", 
      "%d-%m-%y %H:%M:%S", 
      "%d-%m-%y %H:%M:%S.%f", 
      "%d-%m-%y %H:%M", 
      "%d-%m-%y"
    ], 
    "DATE_FORMAT": "d F Y", 
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y", 
      "%Y/%m/%d", 
      "%d-%m-%Y", 
      "%Y-%m-%d", 
      "%d-%m-%y", 
      "%d/%m/%y"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j/F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d/m/Y H:i", 
    "SHORT_DATE_FORMAT": "d/m/Y", 
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

