

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
      "%(sel)s von %(cnt)s ausgew\u00e4hlt", 
      "%(sel)s von %(cnt)s ausgew\u00e4hlt"
    ], 
    "(required):": "(erforderlich):", 
    "6 a.m.": "6 Uhr", 
    "6 p.m.": "18 Uhr", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Wenn Sie neue Dateien hochladen, werden die zuvor hochgeladenen Dateien \u00fcberschrieben. M\u00f6chten Sie dennoch fortfahren?", 
    "April": "April", 
    "Assessment": "Beurteilung", 
    "Assessments": "Beurteilungen", 
    "August": "August", 
    "Available %s": "Verf\u00fcgbare %s", 
    "Back to Full List": "Zur\u00fcck zur kompletten Liste", 
    "Block view is unavailable": "Blockansicht ist nicht verf\u00fcgbar", 
    "Cancel": "Abbrechen", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "\u00c4nderungen an Schritten, die nicht als Teil der Aufgabe ausgew\u00e4hlt sind, werden nicht gespeichert.", 
    "Choose": "Ausw\u00e4hlen", 
    "Choose a Date": "Datum w\u00e4hlen", 
    "Choose a Time": "Uhrzeit w\u00e4hlen", 
    "Choose a time": "Uhrzeit", 
    "Choose all": "Alle ausw\u00e4hlen", 
    "Chosen %s": "Ausgew\u00e4hlte %s", 
    "Click to choose all %s at once.": "Klicken, um alle %s auf einmal auszuw\u00e4hlen.", 
    "Click to remove all chosen %s at once.": "Klicken, um alle ausgew\u00e4hlten %s auf einmal zu entfernen.", 
    "Could not retrieve download url.": "Die Download URL konnte nicht aufgefunden werden.", 
    "Could not retrieve upload url.": "Die Upload-URL konnte nicht aufgefunden werden.", 
    "Couldn't Save This Assignment": "Konnte diese Aufgabe nicht speichern", 
    "Criterion Added": "Kriterium hinzugef\u00fcgt", 
    "Criterion Deleted": "Kriterium gel\u00f6scht", 
    "December": "Dezember", 
    "Describe ": "Beschreibe", 
    "Do you want to upload your file before submitting?": "M\u00f6chten Sie die Datei hochladen, bevor Sie Ihre Antwort einreichen?", 
    "Error": "Fehler", 
    "Error getting the number of ungraded responses": "Fehler bei der Abfrage der Anzahl der unbenoteten Antworten", 
    "February": "Februar", 
    "Feedback available for selection.": "Feedback f\u00fcr die Auswahl verf\u00fcgbar.", 
    "File size must be 10MB or less.": "Datei darf maximal 10MB gro\u00df sein.", 
    "File type is not allowed.": "Dieser Dateityp ist nicht erlaubt. ", 
    "File types can not be empty.": "Dateityp darf nicht leer sein.", 
    "Filter": "Filter", 
    "Final Grade Received": "Erhaltene Endnote", 
    "Heading 3": "\u00dcberschrift 3", 
    "Heading 4": "\u00dcberschrift 4", 
    "Heading 5": "\u00dcberschrift 5", 
    "Heading 6": "\u00dcberschrift 6", 
    "Hide": "Ausblenden", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Wenn Sie diese Seite ohne vorheriges Speichern oder Einreichen der Antwort verlassen, geht die Arbeit an dieser Antwort verloren.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Wenn Sie diese Seite verlassen ohne Ihre Partnerbewertung zu \u00fcbermitteln, werden Sie alle Ihre bis jetzt erledigte Arbeit verlieren.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Wenn Sie diese Seite ohne vorheriges Speichern oder Einreichen der Antwort verlassen, geht die Arbeit an dieser Antwort verloren.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Wenn Sie diese Seite ohne Einreichung der Mitarbeiterbewertung verlassen, geht Ihre Arbeit verloren.", 
    "January": "Januar", 
    "July": "Juli", 
    "June": "Juni", 
    "List of Open Assessments is unavailable": "Liste der offenen Beurteilungen ist nicht verf\u00fcgbar", 
    "March": "M\u00e4rz", 
    "May": "Mai", 
    "Midnight": "Mitternacht", 
    "Noon": "Mittag", 
    "Not Selected": "Nicht ausgew\u00e4hlt", 
    "Note: You are %s hour ahead of server time.": [
      "Achtung: Sie sind %s Stunde der Serverzeit vorraus.", 
      "Achtung: Sie sind %s Stunden der Serverzeit vorraus."
    ], 
    "Note: You are %s hour behind server time.": [
      "Achtung: Sie sind %s Stunde hinter der Serverzeit.", 
      "Achtung: Sie sind %s Stunden hinter der Serverzeit."
    ], 
    "November": "November", 
    "Now": "Jetzt", 
    "October": "Oktober", 
    "One or more rescheduling tasks failed.": "Eine oder mehrere Neuterminierungsaufgaben sind fehlgeschlagen.", 
    "Option Deleted": "Einstellung gel\u00f6scht", 
    "Paragraph": "Absatz", 
    "Peer": "Partner", 
    "Please correct the outlined fields.": "Bitte korrigiere die umrandeten Felder.", 
    "Please wait": "Bitte warten", 
    "Preformatted": "Vorformatiert", 
    "Remove": "Entfernen", 
    "Remove all": "Alle entfernen", 
    "Saving...": "Speichert...", 
    "Self": "Selbst", 
    "September": "September", 
    "Server error.": "Server Problem.", 
    "Show": "Einblenden", 
    "Staff": "Betreuung", 
    "Status of Your Response": "Status Ihrer Antwort", 
    "The display of ungraded and checked out responses could not be loaded.": "Die Anzeige der unbenoteten und ausgecheckten Antworten konnte nicht geladen werden.", 
    "The following file types are not allowed: ": "Die folgenden Dateitypen sind nicht erlaubt:", 
    "The server could not be contacted.": "Der Server konnte nicht erreicht werden.", 
    "The staff assessment form could not be loaded.": "Das Mitarbeiterbewertungsformular konnte nicht geladen werden.", 
    "The submission could not be removed from the grading pool.": "Die Einreichung konnte nicht aus dem Einstufungspool entfernt werden.", 
    "This assessment could not be submitted.": "Diese Bewertung konnte nicht \u00fcbermittelt werden.", 
    "This feedback could not be submitted.": "Diese R\u00fcckmeldung konnte nicht \u00fcbermittelt werden.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Dies ist die Liste der verf\u00fcgbaren %s. Einfach im unten stehenden Feld markieren und mithilfe des \"Ausw\u00e4hlen\"-Pfeils ausw\u00e4hlen.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Dies ist die Liste der ausgew\u00e4hlten %s. Einfach im unten stehenden Feld markieren und mithilfe des \"Entfernen\"-Pfeils wieder entfernen.", 
    "This problem could not be saved.": "Dieses Problem konnte nicht gespeichert werden.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "Diese Fragestellung wurde bereits ver\u00f6ffentlicht. Jegliche \u00c4nderung betrifft nur zuk\u00fcnftige Bewertungen.", 
    "This response could not be saved.": "Diese Antwort konnte nicht gespeichert werden.", 
    "This response could not be submitted.": "Diese Antwort konnte nicht \u00fcbermittelt werden.", 
    "This response has been saved but not submitted.": "Diese Antwort wurde gespeichert, aber nicht \u00fcbermittelt.", 
    "This response has not been saved.": "Diese Antwort wurde nicht gespeichert.", 
    "This section could not be loaded.": "Dieser Abschnitt konnte nicht geladen werden.", 
    "Thumbnail view of ": "Miniaturansicht von", 
    "Today": "Heute", 
    "Tomorrow": "Morgen", 
    "Total Responses": "Gesamte Anzahl Antworten", 
    "Training": "Training", 
    "Type into this box to filter down the list of available %s.": "Durch Eingabe in diesem Feld l\u00e4sst sich die Liste der verf\u00fcgbaren %s eingrenzen.", 
    "Unable to load": "Laden nicht m\u00f6glich", 
    "Unexpected server error.": "Ein unerwarteter Fehler ist aufgetreten.", 
    "Unit Name": "Name der Lerneinheit", 
    "Units": "Lerneinheiten", 
    "Unnamed Option": "Unbenannte Option", 
    "Waiting": "Warten", 
    "Warning": "Warnung", 
    "Yesterday": "Gestern", 
    "You can upload files with these file types: ": "Sie k\u00f6nnen Dateien des folgenden Typs hochladen:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Sie haben ein Kriterium hinzugef\u00fcgt. Sie m\u00fcssen eine Einstellung f\u00fcr dieses Kriterium im Teilnehmertrainingsschritt ausw\u00e4hlen. Klicken Sie hierzu auf den 'Einstellungen'-Tab.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Sie haben ein Kriterium gel\u00f6scht. Das Kriterium wurde aus den Beispielantworten im Teilnehmer\u00fcbungsschritt entfernt.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Sie haben alle Optionen f\u00fcr dieses Kriterium gel\u00f6scht. Das Kriterium wurde aus den Beispielantworten im Teilnehmer\u00fcbungsschritt entfernt.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Sie haben eine Option gel\u00f6scht. Diese Option wurde als Kriterium aus den Beispielantworten im Teilnehmer\u00fcbungsschritt entfernt. Sie m\u00fcssen wahrscheinlich eine neue Option f\u00fcr dieses Kriterium festlegen.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Sie haben eine Aktion ausgew\u00e4hlt, aber keine \u00c4nderungen an bearbeitbaren Feldern vorgenommen. Sie wollten wahrscheinlich auf \"Ausf\u00fchren\" und nicht auf \"Speichern\" klicken.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Sie haben eine Aktion ausgew\u00e4hlt, aber ihre vorgenommenen \u00c4nderungen nicht gespeichert. Klicken Sie OK, um dennoch zu speichern. Danach m\u00fcssen Sie die Aktion erneut ausf\u00fchren.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Sie haben \u00c4nderungen an bearbeitbaren Feldern vorgenommen und nicht gespeichert. Wollen Sie die Aktion trotzdem ausf\u00fchren und Ihre \u00c4nderungen verwerfen?", 
    "You must provide a learner name.": "Name erforderlich", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Sie sind dabei Ihre Antwort f\u00fcr diese Aufgabe einzureichen. Nachdem Sie Ihre Antwort abgeschickt haben, k\u00f6nnen Sie diese nicht mehr \u00e4ndern und auch keine neue Antwort geben.", 
    "Your file ": "Ihre Datei", 
    "one letter Friday\u0004F": "Fr", 
    "one letter Monday\u0004M": "Mo", 
    "one letter Saturday\u0004S": "Sa", 
    "one letter Sunday\u0004S": "So", 
    "one letter Thursday\u0004T": "Do", 
    "one letter Tuesday\u0004T": "Di", 
    "one letter Wednesday\u0004W": "Mi"
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
    "DATETIME_FORMAT": "j. F Y H:i", 
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
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j. F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i", 
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

