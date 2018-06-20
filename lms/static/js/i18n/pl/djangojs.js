

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n==1 ? 0 : (n%10>=2 && n%10<=4) && (n%100<12 || n%100>=14) ? 1 : n!=1 && (n%10>=0 && n%10<=1) || (n%10>=5 && n%10<=9) || (n%100>=12 && n%100<=14) ? 2 : 3);
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
      "Zaznaczono %(sel)s z %(cnt)s", 
      "Zaznaczono %(sel)s z %(cnt)s", 
      "Zaznaczono %(sel)s z %(cnt)s", 
      "Zaznaczono %(sel)s z %(cnt)s"
    ], 
    "(required):": "(wymagany):", 
    "6 a.m.": "6 rano", 
    "6 p.m.": "6 po po\u0142udniu", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Po przes\u0142aniu nowych plik\u00f3w, wszystkie twoje wcze\u015bniej wgrane pliki zostan\u0105 podmienione. Czy kontynuowa\u0107?", 
    "April": "Kwiecie\u0144", 
    "Assessment": "Ocena", 
    "Assessments": "Oceny", 
    "August": "Sierpie\u0144", 
    "Available %s": "Dost\u0119pne %s", 
    "Back to Full List": "Powr\u00f3t do pe\u0142nej listy", 
    "Block view is unavailable": "Podgl\u0105d bloku jest niedost\u0119pny", 
    "Cancel": "Anuluj", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Zmiany w krokach, kt\u00f3re nie zosta\u0142y wybrane jako elementy zadania, nie zostan\u0105 zapisane.", 
    "Choose": "Wybierz", 
    "Choose a Date": "Wybierz Dat\u0119", 
    "Choose a Time": "Wybierz Czas", 
    "Choose a time": "Wybierz czas", 
    "Choose all": "Wybierz wszystkie", 
    "Chosen %s": "Wybrane %s", 
    "Click to choose all %s at once.": "Kliknij, aby wybra\u0107 jednocze\u015bnie wszystkie %s.", 
    "Click to remove all chosen %s at once.": "Kliknij, aby usun\u0105\u0107 jednocze\u015bnie wszystkie wybrane %s.", 
    "Could not retrieve download url.": "Nie mo\u017cna odczyta\u0107 adresu URL pobierania.", 
    "Could not retrieve upload url.": "Nie mo\u017cna odczyta\u0107 adresu URL uploadu.", 
    "Couldn't Save This Assignment": "Nie uda\u0142o si\u0119 zapisa\u0107 tego zadania", 
    "Criterion Added": "Dodano kryterium", 
    "Criterion Deleted": "Kryterium usuni\u0119te", 
    "December": "Grudzie\u0144", 
    "Describe ": "Opis", 
    "Do you want to upload your file before submitting?": "Czy chcesz wgra\u0107 sw\u00f3j plik przed wys\u0142aniem odpowiedzi?", 
    "Error": "B\u0142\u0105d", 
    "Error getting the number of ungraded responses": "Wyst\u0105pi\u0142 b\u0142\u0105d podczas uzyskiwania liczby nieocenionych prac.", 
    "February": "Luty", 
    "Feedback available for selection.": "Komentarz zwrotny dost\u0119pny do wyboru.", 
    "File size must be 10MB or less.": "Rozmiar pliku nie mo\u017ce przekroczy\u0107 10MB.", 
    "File type is not allowed.": "Ten typ pliku jest niedozwolony.", 
    "File types can not be empty.": "Typy plik\u00f3w nie mog\u0105 by\u0107 puste.", 
    "Filter": "Filtr", 
    "Final Grade Received": "Uzyskana ocena ko\u0144cowa", 
    "Hide": "Ukryj", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Je\u017celi opu\u015bcisz t\u0119 stron\u0119 bez zapisania lub przes\u0142ania swojej odpowiedzi, stracisz ca\u0142\u0105 swoj\u0105 prac\u0119.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Je\u017celi opu\u015bcisz t\u0119 stron\u0119 bez przes\u0142ania zadania do oceny, stracisz ca\u0142\u0105 swoj\u0105 prac\u0119.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Je\u017celi opu\u015bcisz t\u0119 stron\u0119 bez przes\u0142ania swojego zadania, stracisz ca\u0142\u0105 swoj\u0105 prac\u0119.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Je\u017celi opu\u015bcisz t\u0119 stron\u0119 bez przes\u0142ania oceny, stracisz ca\u0142\u0105 swoj\u0105 prac\u0119.", 
    "January": "Stycze\u0144", 
    "July": "Lipiec", 
    "June": "Czerwiec", 
    "List of Open Assessments is unavailable": "Lista otwartych ocen jest niedost\u0119pna", 
    "March": "Marzec", 
    "May": "Maj", 
    "Midnight": "P\u00f3\u0142noc", 
    "Noon": "Po\u0142udnie", 
    "Not Selected": "Nie wybrane", 
    "Note: You are %s hour ahead of server time.": [
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godzin\u0119 do przodu w stosunku do czasu serwera.", 
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godziny do przodu w stosunku do czasu serwera.", 
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godzin do przodu w stosunku do czasu serwera.", 
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godzin do przodu w stosunku do czasu serwera."
    ], 
    "Note: You are %s hour behind server time.": [
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godzin\u0119 do ty\u0142u w stosunku do czasu serwera.", 
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godziny do ty\u0142u w stosunku do czasu serwera.", 
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godzin do ty\u0142u w stosunku do czasu serwera.", 
      "Uwaga: Czas lokalny jest przesuni\u0119ty o %s godzin do ty\u0142u w stosunku do czasu serwera."
    ], 
    "November": "Listopad", 
    "Now": "Teraz", 
    "October": "Pa\u017adziernik", 
    "One or more rescheduling tasks failed.": "Jedna lub wi\u0119cej czynno\u015b\u0107 zmiany termin\u00f3w nie powiod\u0142a si\u0119.", 
    "Option Deleted": "Opcja usuni\u0119ta", 
    "Peer": "Przez innych kursant\u00f3w", 
    "Please correct the outlined fields.": "Prosz\u0119 poprawi\u0107 zaznaczone pola.", 
    "Please wait": "Prosz\u0119 czeka\u0107", 
    "Remove": "Usu\u0144", 
    "Remove all": "Usu\u0144 wszystkie", 
    "Saving...": "Zapisywanie...", 
    "Self": "Samodzielnie", 
    "September": "Wrzesie\u0144", 
    "Server error.": "B\u0142\u0105d serwera", 
    "Show": "Poka\u017c", 
    "Staff": "Kadra", 
    "Status of Your Response": "Status twojej odpowiedzi", 
    "The display of ungraded and checked out responses could not be loaded.": "Nie uda\u0142o si\u0119 wy\u015bwietli\u0107 listy nieocenionych i sprawdzonych odpowiedzi.", 
    "The following file types are not allowed: ": "Nast\u0119puj\u0105ce typy plik\u00f3w s\u0105 niedozwolone:", 
    "The server could not be contacted.": "Nie uda\u0142o si\u0119 po\u0142\u0105czy\u0107 z serwerem.", 
    "The staff assessment form could not be loaded.": "Nie uda\u0142o si\u0119 wczyta\u0107 formularza oceny kadry.", 
    "The submission could not be removed from the grading pool.": "Zg\u0142oszenie nie mo\u017ce zosta\u0107 usuni\u0119te z puli oceniania.", 
    "This assessment could not be submitted.": "Nie uda\u0142o si\u0119 wys\u0142a\u0107 tej oceny.", 
    "This feedback could not be submitted.": "Nie uda\u0142o si\u0119 wys\u0142a\u0107 tej opinii.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "To lista dost\u0119pnych %s. Aby wybra\u0107 pozycje, zaznacz je i kliknij strza\u0142k\u0119 \u201eWybierz\u201d pomi\u0119dzy listami.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "To lista wybranych %s. Aby usun\u0105\u0107, zaznacz pozycje wybrane do usuni\u0119cia i kliknij strza\u0142k\u0119 \u201eUsu\u0144\u201d pomi\u0119dzy listami.", 
    "This problem could not be saved.": "Nie uda\u0142o si\u0119 zapisa\u0107 \u0107wiczenia.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "To \u0107wiczenie zosta\u0142o ju\u017c opublikowane. Jakiekolwiek zmiany b\u0119d\u0105 obowi\u0105zywa\u0107 tylko dla przysz\u0142ych ocen.", 
    "This response could not be saved.": "Nie uda\u0142o si\u0119 zapisa\u0107 tej odpowiedzi.", 
    "This response could not be submitted.": "Nie uda\u0142o si\u0119 wys\u0142a\u0107 tej odpowiedzi.", 
    "This response has been saved but not submitted.": "Ta odpowied\u017a zosta\u0142a zapisania, lecz nie zosta\u0142a wys\u0142ana.", 
    "This response has not been saved.": "Ta odpowied\u017a nie zosta\u0142a zapisana.", 
    "This section could not be loaded.": "Nie uda\u0142o si\u0119 wczyta\u0107 tej sekcji.", 
    "Thumbnail view of ": "Ikonka pliku", 
    "Today": "Dzisiaj", 
    "Tomorrow": "Jutro", 
    "Total Responses": "Suma odpowiedzi", 
    "Training": "Trening", 
    "Type into this box to filter down the list of available %s.": "Wpisz co\u015b tutaj, aby wyfiltrowa\u0107 list\u0119 dost\u0119pnych %s.", 
    "Unable to load": "Nie uda\u0142o si\u0119 wczyta\u0107", 
    "Unexpected server error.": "Niespodziewany b\u0142\u0105d serwera.", 
    "Unit Name": "Nazwa lekcji", 
    "Units": "Lekcje", 
    "Unnamed Option": "Bezimienna opcja", 
    "Waiting": "Oczekuje", 
    "Warning": "Ostrze\u017cenie", 
    "Yesterday": "Wczoraj", 
    "You can upload files with these file types: ": "Mo\u017cesz wgra\u0107 pliki o nast\u0119puj\u0105cych formatach:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Doda\u0142e\u015b kryterium. Musisz teraz wybra\u0107 opcj\u0119 dla kryterium z poziomu Szkolenia Studenta. Aby to zrobi\u0107, kliknij na Ustawienia.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Usun\u0105\u0142e\u015b kryterium. Tak wi\u0119c kryterium zosta\u0142o usuni\u0119te z przyk\u0142adowych odpowiedzi w Szkoleniu Studenta.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Usun\u0105\u0142e\u015b wszystkie opcje dla tego kryterium. Tak wi\u0119c kryterium zosta\u0142o usuni\u0119te z przyk\u0142adowych odpowiedzi w Szkoleniu Studenta.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Usun\u0105\u0142e\u015b opcj\u0119. Ta opcja zosta\u0142a usuni\u0119ta z kryterium w przyk\u0142adowych odpowiedziach w Szkoleniu Studenta. By\u0107 mo\u017ce musisz teraz wybra\u0107 now\u0105 opcj\u0119 dla tego kryterium.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Wybrano akcj\u0119, lecz nie dokonano \u017cadnych zmian w polach. Prawdopodobnie szukasz przycisku \u201eWykonaj\u201d, a nie \u201eZapisz\u201d.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Wybrano akcj\u0119, lecz cz\u0119\u015b\u0107 zmian w polach nie zosta\u0142a zachowana. Kliknij OK, aby zapisa\u0107. Aby wykona\u0107 akcj\u0119, nale\u017cy j\u0105 ponownie uruchomi\u0107.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Zmiany w niekt\u00f3rych polach nie zosta\u0142y zachowane. Po wykonaniu akcji, zmiany te zostan\u0105 utracone.", 
    "You must provide a learner name.": "Musisz poda\u0107 nazw\u0119 ucz\u0105cego si\u0119.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Wysy\u0142asz odpowied\u017a na zadanie. Po wys\u0142aniu nie b\u0119dziesz m\u00f3g\u0142 jej zmieni\u0107, ani wys\u0142a\u0107 nowej odpowiedzi.", 
    "one letter Friday\u0004F": "P", 
    "one letter Monday\u0004M": "P", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "N", 
    "one letter Thursday\u0004T": "C", 
    "one letter Tuesday\u0004T": "W", 
    "one letter Wednesday\u0004W": "\u015a"
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
    "DATETIME_FORMAT": "j E Y H:i", 
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
    "DATE_FORMAT": "j E Y", 
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y", 
      "%d.%m.%y", 
      "%y-%m-%d", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d-m-Y  H:i", 
    "SHORT_DATE_FORMAT": "d-m-Y", 
    "THOUSAND_SEPARATOR": "\u00a0", 
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

