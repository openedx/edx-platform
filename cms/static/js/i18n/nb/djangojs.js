

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
    "\n          Start my exam\n        ": "\n          Start min eksamen\n        ",
    "\n        If you take this exam without proctoring, you will <strong> no longer be eligible for academic credit. </strong>\n      ": "\n        Dersom du gjennomf\u00f8rer denne eksamenen uten overv\u00e5kning, vil du <strong> ikke lenger ha grunnlag for  formell kompetanse \"academic credit\". </strong>\n      ",
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      Er du sikker p\u00e5 at du vil avslutte din overv\u00e5kete eksamen?\n    ",
    "\n      Error with proctored exam\n    ": "\n      Feil med overv\u00e5ket eksamen\n    ",
    "\n      Follow these instructions\n    ": "\n      F\u00f8lg disse instruksjonene\n    ",
    "\n      This exam is proctored\n    ": "\n      Denne eksamenen er overv\u00e5ket\n    ",
    "\n      Try a proctored exam\n    ": "\n      Fors\u00f8k en overv\u00e5ket eksamen\n    ",
    "\n      Yes, end my proctored exam\n    ": "\n Ja, avslutt min overv\u00e5kete eksamen\n ",
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n    %(exam_name)s er en eksamen med tidsfrist (%(total_time)s)\n    ",
    " Your Proctoring Session Has Started ": "Din overv\u00e5kede sesjon har startet",
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s av %(cnt)s valgt",
      "%(sel)s av %(cnt)s valgt"
    ],
    "(required):": "(n\u00f8dvendig):",
    "6 a.m.": "06:00",
    "6 p.m.": "18:00",
    "Additional Time (minutes)": "Ekstra tid (minutter)",
    "All Unreviewed": "Alle som ikke er gjennomg\u00e5tt",
    "All Unreviewed Failures": "Feil ved alle som ikke er gjennomg\u00e5tt",
    "April": "April",
    "Assessment": "Vurdering",
    "Assessments": "Vurderinger",
    "August": "August",
    "Available %s": "Tilgjengelige %s",
    "Back to Full List": "Tilbake til hele listen",
    "Block view is unavailable": "Blokkvisning er utilgjengelig",
    "Cancel": "Avbryt",
    "Cannot Start Proctored Exam": "Kan ikke starte overv\u00e5ket eksamen",
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Endringer i trinn som ikke er valgt som en del av oppgaven, blir ikke lagret.",
    "Choose": "Velg",
    "Choose a Date": "Velg en dato",
    "Choose a Time": "Velg et klokkeslett",
    "Choose a time": "Velg et klokkeslett",
    "Choose all": "Velg alle",
    "Chosen %s": "Valgte %s",
    "Click to choose all %s at once.": "Klikk for \u00e5 velge alle %s samtidig",
    "Click to remove all chosen %s at once.": "Klikk for \u00e5 fjerne alle valgte %s samtidig",
    "Close": "Lukk",
    "Continue Exam Without Proctoring": "Fortsett eksamen uten overv\u00e5kning",
    "Continue to Verification": "Fortsett til verifisering",
    "Continue to my practice exam": "Fortsett til min pr\u00f8veeksamen",
    "Could not retrieve download url.": "Kunne ikke hente nedlastings url.",
    "Could not retrieve upload url.": "Kunne ikke hente opplastings url.",
    "Couldn't Save This Assignment": "Kunne ikke lagre denne oppgaven",
    "Course Id": "KursID",
    "Created": "Opprettet",
    "Criterion Added": "Kriteria lagt til",
    "Criterion Deleted": "Kriterie slettet",
    "December": "Desember",
    "Declined": "Avsl\u00e5tt",
    "Describe ": "Beskriv",
    "Do you want to upload your file before submitting?": "Vil du laste opp filen din f\u00f8r du sender inn?",
    "Download Software Clicked": "Last ned programvare klikket",
    "Error": "Feil",
    "Error getting the number of ungraded responses": "Det oppstod en feil ved fors\u00f8k p\u00e5 \u00e5 finne antall ikke-rettede svar",
    "Failed Proctoring": "Overv\u00e5kningen ikke godkjent",
    "February": "Februar",
    "Feedback available for selection.": "Tilbakemelding kan velges.",
    "File types can not be empty.": "Filtyper kan ikke v\u00e6re tomme.",
    "Filter": "Filter",
    "Final Grade Received": "Endelig karakter oppn\u00e5dd",
    "Go Back": "G\u00e5 tilbake",
    "Heading 3": "Overskrift 3",
    "Heading 4": "Overskrift 4",
    "Heading 5": "Overskrift 5",
    "Heading 6": "Overskrift 6",
    "Hide": "Skjul",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Hvis du forlater denne siden uten \u00e5 lagre eller sende inn svaret ditt, vil alt arbeid du har gjort p\u00e5 svaret ditt g\u00e5 tapt.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Dersom du forlater denne siden uten \u00e5 levere din hverandrevurdering, vil det arbeidet du har gjort g\u00e5 tapt.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Dersom du forlater denne siden uten \u00e5 levere din egenvurdering, vil du miste alt arbeidet du har gjort.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Dersom du forlater denne siden uten \u00e5 levere din personal-vurdering, vil du miste alt arbeidet du har gjort.",
    "Is Sample Attempt": "Er eksempel p\u00e5 gjennomf\u00f8ring",
    "January": "Januar",
    "July": "Juli",
    "June": "Juni",
    "List of Open Assessments is unavailable": "Liste over \u00e5pne vurderinger er ikke tilgjengelig",
    "March": "Mars",
    "May": "Mai",
    "Midnight": "Midnatt",
    "Noon": "12:00",
    "Not Selected": "Ikke valgt",
    "Note: You are %s hour ahead of server time.": [
      "Merk: Du er %s time foran server-tid.",
      "Merk: Du er %s timer foran server-tid."
    ],
    "Note: You are %s hour behind server time.": [
      "Merk: Du er %s time bak server-tid.",
      "Merk: Du er %s timer bak server-tid."
    ],
    "November": "November",
    "Now": "N\u00e5",
    "October": "Oktober",
    "One or more rescheduling tasks failed.": "Ett eller flere fors\u00f8k p\u00e5 ombooking feilet.",
    "Option Deleted": "Opsjon slettet",
    "Paragraph": "Avsnitt",
    "Passed Proctoring": "Best\u00e5tt overv\u00e5kning",
    "Peer": "Likemann",
    "Please correct the outlined fields.": "Vennligst rett opp de uthevede feltene.",
    "Please wait": "Vennligst vent",
    "Practice Exam Completed": "Pr\u00f8veeksamen er gjennomf\u00f8rt",
    "Practice Exam Failed": "Pr\u00f8veeksamen ikke best\u00e5tt",
    "Preformatted": "Forh\u00e5ndsformatert",
    "Proctored Option Available": "Overv\u00e5ket alternativ tilgjengelig",
    "Proctored Option No Longer Available": "Overv\u00e5ket alternativ ikke lenger tilgjengelig",
    "Ready To Start": "Klar for \u00e5 starte",
    "Ready To Submit": "Klar for innlevering",
    "Rejected": "Avvist",
    "Remove": "Slett",
    "Remove all": "Fjern alle",
    "Retry Verification": "Fors\u00f8k verifisering p\u00e5 nytt",
    "Saving...": "Lagrer...",
    "Second Review Required": "Ytterligere gjennomgang n\u00f8dvendig",
    "Self": "Selv",
    "September": "September",
    "Server error.": "Serverfeil.",
    "Show": "Vis",
    "Staff": "Personell",
    "Start System Check": "Start systemsjekk",
    "Started": "Startet",
    "Status of Your Response": "Status p\u00e5 ditt svar",
    "Submitted": "Levert",
    "Taking As Open Exam": "Tas som \u00e5pen eksamen",
    "Taking As Proctored Exam": "Gjennomf\u00f8rer som overv\u00e5ket eksamen",
    "Taking as Proctored": "Gjennomf\u00f8res som overv\u00e5ket",
    "The display of ungraded and checked out responses could not be loaded.": "Visning av ikke-vurderte og avklarte svar kunne ikke lastes inn.",
    "The following file types are not allowed: ": "F\u00f8lgende filtyper er ikke tillatt:",
    "The server could not be contacted.": "Serveren kan ikke kontaktes.",
    "The staff assessment form could not be loaded.": "Personalets vurderingsskjema kunne ikke lastes inn.",
    "The submission could not be removed from the grading pool.": "Innleveringen kunne ikke fjernes fra karaktersettingsoversikten.",
    "This assessment could not be submitted.": "Denne vurderingen kunne ikke leveres.",
    "This feedback could not be submitted.": "Denne tilbakemeldingen kunne ikke leveres.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Dette er listen over tilgjengelige %s. Du kan velge noen ved \u00e5 markere de i boksen under og s\u00e5 klikke p\u00e5 \"Velg\"-pilen mellom de to boksene.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Dette er listen over valgte %s. Du kan fjerne noen ved \u00e5 markere de i boksen under og s\u00e5 klikke p\u00e5 \"Fjern\"-pilen mellom de to boksene.",
    "This problem could not be saved.": "Dette problemet kunne ikke lagres.",
    "This problem has already been released. Any changes will apply only to future assessments.": "Dette problemet har allerede blitt utgitt. Enhver endringer vil kun gjelde for kommende vurderinger.",
    "This response could not be saved.": "Dette svaret kunne ikke bli lagret.",
    "This response could not be submitted.": "Dette svaret kunne ikke leveres.",
    "This response has been saved but not submitted.": "Svaret har blitt lagret men er ikke innlevert.",
    "This response has not been saved.": "Dette svaret har ikke blitt lagret.",
    "This section could not be loaded.": "Denne delen kunne ikke lastes inn.",
    "Thumbnail view of ": "Miniatyrbilde av",
    "Timed Exam": "Eksamen med tidsfrist",
    "Timed Out": "Timet ut",
    "Today": "I dag",
    "Tomorrow": "I morgen",
    "Total Responses": "Totalt antall svar",
    "Training": "\u00d8ver",
    "Try this practice exam again": "Gjennomf\u00f8r denne pr\u00f8veeksamenen p\u00e5 nytt",
    "Type into this box to filter down the list of available %s.": "Skriv i dette feltet for \u00e5 filtrere ned listen av tilgjengelige %s.",
    "Unable to load": "Ikke i stand til \u00e5 laste",
    "Unexpected server error.": "Uventet serverfeil.",
    "Ungraded Practice Exam": "Pr\u00f8veeksamen som ikke rettes",
    "Unit Name": "Navn p\u00e5 enheten",
    "Units": "Enheter",
    "Unnamed Option": "Alternativ uten navn",
    "Verified": "Bekreftet",
    "View my exam": "Se min eksamen",
    "Waiting": "Venter",
    "Warning": "Advarsel",
    "Yesterday": "I g\u00e5r",
    "You can also retry this practice exam": "Du kan ogs\u00e5 fors\u00f8ke denne pr\u00f8veeksamenen p\u00e5 nytt",
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Du har lagt til et kriterium. Du m\u00e5 velge et alternativ for kriteriet i \"Learner Training\" trinnet. For \u00e5 gj\u00f8re dette, klikk p\u00e5 Innstillinger-fanen.",
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Du har slettet et kriterium. Kriteriet er fjernet fra eksempelresponsene i \"Learner Training\" trinnet.",
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Du har slettet alle alternativene for dette kriteriet. Kriteriet er fjernet fra eksempelsvarene i \"Learner Training\" trinnet.",
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Du har slettet et alternativ. Dette alternativet er fjernet fra kriteriet i pr\u00f8veresponsene i \"Learner Training\" trinnet. Du m\u00e5 kanskje velge et nytt alternativ for kriteriet.",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Du har valgt en handling, og har ikke gjort noen endringer i individuelle felter. Du ser mest sannsynlig etter G\u00e5-knappen, ikke Lagre-knappen.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Du har valgt en handling, men du har ikke lagret dine endringer i individuelle felter enda. Vennligst trykk OK for \u00e5 lagre. Du m\u00e5 utf\u00f8re handlingen p\u00e5 nytt.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Du har ulagrede endringer i individuelle felter. Hvis du utf\u00f8rer en handling, vil dine ulagrede endringer g\u00e5 tapt.",
    "You must provide a learner name.": "Du m\u00e5 oppgi et navn p\u00e5 kursdeltager.",
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Du er i ferd med \u00e5 levere ditt svar p\u00e5 denne oppgaven. Etter at du leverer svaret kan du ikke endre det eller levere et nytt svar.",
    "Your file ": "Din fil",
    "active proctored exams": "aktive overv\u00e5kete eksamener",
    "courses with active proctored exams": "kurs med aktive overv\u00e5kete eksamener",
    "internally reviewed": "gjennomg\u00e5tt internt",
    "one letter Friday\u0004F": "F",
    "one letter Monday\u0004M": "M",
    "one letter Saturday\u0004S": "L",
    "one letter Sunday\u0004S": "S",
    "one letter Thursday\u0004T": "T",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "O",
    "pending": "venter",
    "satisfactory": "tilfredsstillende",
    "unsatisfactory": "ikke tilfredsstillende",
    "your course": "ditt kurs"
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
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
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
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d",
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H:%M",
      "%d.%m.%Y",
      "%d.%m.%y %H:%M:%S",
      "%d.%m.%y %H:%M:%S.%f",
      "%d.%m.%y %H:%M",
      "%d.%m.%y"
    ],
    "DATE_FORMAT": "j. F Y",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%d.%m.%Y",
      "%d.%m.%y"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
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

