

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2;
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
      "%(sel)s z %(cnt)s vybran\u00e9", 
      "%(sel)s z %(cnt)s vybran\u00e9", 
      "%(sel)s z %(cnt)s vybran\u00fdch"
    ], 
    "6 a.m.": "6:00", 
    "Available %s": "Dostupn\u00e9 %s", 
    "Cancel": "Zru\u0161i\u0165", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Zmeny pre kroky, ktor\u00e9 nie s\u00fa zvolen\u00e9 ako s\u00fa\u010das\u0165 tohto zadania, nebud\u00fa ulo\u017een\u00e9.", 
    "Choose": "Vybra\u0165", 
    "Choose a time": "Vybra\u0165 \u010das", 
    "Choose all": "Vybra\u0165 v\u0161etko", 
    "Chosen %s": "Vybran\u00e9 %s", 
    "Click to choose all %s at once.": "Kliknite sem pre vybratie v\u0161etk\u00fdch %s naraz.", 
    "Click to remove all chosen %s at once.": "Kliknite sem pre vymazanie vybrat\u00fdch %s naraz.", 
    "Could not retrieve download url.": "Nebolo mo\u017en\u00e9 z\u00edska\u0165 adresu pre prevzatie obsahu.", 
    "Could not retrieve upload url.": "Nebolo mo\u017en\u00e9 z\u00edska\u0165 url adresu pre odovzdanie obsahu.", 
    "Couldn't Save This Assignment": "Toto zadanie nie je mo\u017en\u00e9 ulo\u017ei\u0165", 
    "Criterion Added": "Pridan\u00e9 krit\u00e9rium", 
    "Criterion Deleted": "Krit\u00e9rium odstr\u00e1nen\u00e9", 
    "Do you want to upload your file before submitting?": "Chcete pred odoslan\u00edm odovzda\u0165 v\u00e1\u0161 s\u00fabor?", 
    "Error": "Chyba", 
    "File type is not allowed.": "Typ s\u00faboru nie je povolen\u00fd.", 
    "File types can not be empty.": "Typy s\u00faborov nem\u00f4\u017eu by\u0165 pr\u00e1zdne.", 
    "Filter": "Filtrova\u0165", 
    "Hide": "Skry\u0165", 
    "Midnight": "Polnoc", 
    "Noon": "Poludnie", 
    "Not Selected": "Nie je vybran\u00e9", 
    "Note: You are %s hour ahead of server time.": [
      "Pozn\u00e1mka: Ste %s hodinu pred \u010dasom servera.", 
      "Pozn\u00e1mka: Ste %s hodiny pred \u010dasom servera.", 
      "Pozn\u00e1mka: Ste %s hod\u00edn pred \u010dasom servera."
    ], 
    "Note: You are %s hour behind server time.": [
      "Pozn\u00e1mka: Ste %s hodinu za \u010dasom servera.", 
      "Pozn\u00e1mka: Ste %s hodiny za \u010dasom servera.", 
      "Pozn\u00e1mka: Ste %s hod\u00edn za \u010dasom servera."
    ], 
    "Now": "Teraz", 
    "One or more rescheduling tasks failed.": "Jedna alebo viac \u00faloh pre zmenu term\u00ednu zlyhala.", 
    "Option Deleted": "Vo\u013eba odstr\u00e1nen\u00e1", 
    "Please correct the outlined fields.": "Opravte, pros\u00edm, zv\u00fdraznen\u00e9 polia.", 
    "Remove": "Odstr\u00e1ni\u0165", 
    "Remove all": "Odstr\u00e1ni\u0165 v\u0161etky", 
    "Saving...": "Uklad\u00e1 sa...", 
    "Show": "Zobrazi\u0165", 
    "Status of Your Response": "Stav va\u0161ej odpovede", 
    "The following file types are not allowed: ": "Nasleduj\u00face typy s\u00faborov nie s\u00fa povolen\u00e9:", 
    "The server could not be contacted.": "Nebolo mo\u017en\u00e9 kontaktova\u0165 server.", 
    "The submission could not be removed from the grading pool.": "Toto podanie nebolo mo\u017en\u00e9 odstr\u00e1ni\u0165 z klasifika\u010dn\u00e9ho h\u00e1rku.", 
    "This assessment could not be submitted.": "Toto hodnotenie nie je mo\u017en\u00e9 odosla\u0165.", 
    "This feedback could not be submitted.": "T\u00fato sp\u00e4tn\u00fa v\u00e4zbu nie je mo\u017en\u00e9 odosla\u0165.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre v\u00fdber je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \"Vybra\u0165\" presun\u00fa\u0165.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Toto je zoznam dostupn\u00fdch %s. Pre vymazanie je potrebn\u00e9 ozna\u010di\u0165 ich v poli a n\u00e1sledne kliknut\u00edm na \u0161\u00edpku \"Vymaza\u0165\" vymaza\u0165.", 
    "This problem could not be saved.": "T\u00fato \u00falohu nebolo mo\u017en\u00e9 ulo\u017ei\u0165.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "T\u00e1to \u00faloha u\u017e bola vydan\u00e1. Ak\u00e1ko\u013evek zmena sa t\u00fdka len bud\u00facich hodnoten\u00ed.", 
    "This response could not be saved.": "T\u00fato odpove\u010f nie je mo\u017en\u00e9 ulo\u017ei\u0165.", 
    "This response could not be submitted.": "T\u00fato odpove\u010f nie je mo\u017en\u00e9 odosla\u0165.", 
    "This response has been saved but not submitted.": "T\u00e1to odpove\u010f bola ulo\u017een\u00e1, ale nebola odoslan\u00e1.", 
    "This response has not been saved.": "Odpove\u010f nebola ulo\u017een\u00e1.", 
    "This section could not be loaded.": "T\u00fato sekciu nie je mo\u017en\u00e9 na\u010d\u00edta\u0165.", 
    "Today": "Dnes", 
    "Tomorrow": "Zajtra", 
    "Type into this box to filter down the list of available %s.": "P\u00ed\u0161te do tohto po\u013ea pre vyfiltrovanie dostupn\u00fdch %s.", 
    "Unnamed Option": "Nepomenovan\u00e1 vo\u013eba", 
    "Warning": "Upozornenie", 
    "Yesterday": "V\u010dera", 
    "You can upload files with these file types: ": "M\u00f4\u017eete odovzd\u00e1va\u0165 s\u00fabory t\u00fdchto typov:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Pridali ste krit\u00e9rium. Pre toto krit\u00e9rium si mus\u00edte zvoli\u0165 vo\u013ebu v kroku V\u00fdcvik \u0161tudentov. Aby ste tak mohli spravi\u0165, kliknite na kartu Nastavenia.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Odstr\u00e1nili ste krit\u00e9rium. Toto krit\u00e9rium bolo vymazan\u00e9 zo v\u0161etk\u00fdch vzorov\u00fdch odpoved\u00ed v kroku V\u00fdcvik \u0161tudentov.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Odstr\u00e1nili ste v\u0161etky vo\u013eby pre toto krit\u00e9rium. Toto krit\u00e9rium bolo vymazan\u00e9 zo v\u0161etk\u00fdch vzorov\u00fdch odpoved\u00ed v kroku V\u00fdcvik \u0161tudentov.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Odstr\u00e1nili ste vo\u013ebu. T\u00e1to vo\u013eba bola vymazan\u00e1 z pridru\u017een\u00e9ho krit\u00e9ria vo vzorov\u00fdch odpovediach v koku V\u00fdcvik \u0161tudentov. Pravdepodobne budete musie\u0165 pre toto krit\u00e9rium zvoli\u0165 nov\u00fa vo\u013ebu.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Vybrali ste akciu, ale neurobili ste \u017eiadne zmeny v jednotliv\u00fdch poliach. Pravdepodobne ste chceli pou\u017ei\u0165 tla\u010didlo vykona\u0165 namiesto ulo\u017ei\u0165.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Vybrali ste akciu, ale neulo\u017eili ste jednotliv\u00e9 polia. Pros\u00edm, ulo\u017ete zmeny kliknut\u00edm na OK. Akciu budete musie\u0165 vykona\u0165 znova.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Vr\u00e1mci jednotliv\u00fdch editovate\u013en\u00fdch pol\u00ed m\u00e1te neulo\u017een\u00e9 zmeny. Ak vykon\u00e1te akciu, va\u0161e zmeny bud\u00fa straten\u00e9.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Chyst\u00e1te sa odosla\u0165 va\u0161u odpove\u010f pre toto zadanie. Potom ako t\u00fato odpove\u010f odo\u0161lete, nebudete ju m\u00f4c\u0165 zmeni\u0165 ani nebudete m\u00f4c\u0165 odosla\u0165 nov\u00fa odpove\u010f."
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
    "DATETIME_FORMAT": "j. F Y G:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S", 
      "%d.%m.%Y %H:%M:%S.%f", 
      "%d.%m.%Y %H:%M", 
      "%d.%m.%Y", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d"
    ], 
    "DATE_FORMAT": "j. F Y", 
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y", 
      "%d.%m.%y", 
      "%y-%m-%d", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j. F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d.m.Y G:i", 
    "SHORT_DATE_FORMAT": "d.m.Y", 
    "THOUSAND_SEPARATOR": "\u00a0", 
    "TIME_FORMAT": "G:i", 
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

