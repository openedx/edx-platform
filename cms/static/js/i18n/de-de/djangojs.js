

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
    "\n\nThis email is to let you know that the status of your proctoring session review for %(exam_name)s in\n<a href=\"%(course_url)s\">%(course_name)s </a> is %(status)s. If you have any questions about proctoring,\ncontact %(platform)s support at %(contact_email)s.\n\n": "\n\nIn dieser E-Mail erfahren Sie den Stand Ihrer Aufsichtssitzung der Reviews f\u00fcr %(exam_name)s in\n<a href=\"%(course_url)s\">%(course_name)s </a> is %(status)s. Falls Sie weitere Fragen zur Aufsicht haben,\nkontaktieren Sie den %(platform)s Support unter %(contact_email)s.\n\n", 
    "\n                    Make sure you are on a computer with a webcam, and that you have valid photo identification\n                    such as a driver's license or passport, before you continue.\n                ": "\nStellen Sie sicher, dass Sie sich auf einem Computer mit einer Webcam befinden und dass Sie sich mit einem g\u00fcltigen Lichtbildausweis ausweisen k\u00f6nnen.\n beispielsweise ein F\u00fchrerschein oder ein Personalausweis.", 
    "\n                    Your verification attempt failed. Please read our guidelines to make\n                    sure you understand the requirements for successfully completing verification,\n                    then try again.\n                ": "\n                    Ihr Versuch zur Verifikation ist fehlgeschlagen. Bitte Lesen Sie\nunsere Richtlinien um sicher zu gehen, dass Sie die Anforderungen f\u00fcr eine erfolgreiche Durchf\u00fchrung der verifikation verstanden haben.\nBitte versuchen Sie es dann noch einmal.\n                ", 
    "\n                    Your verification has expired. You must successfully complete a new identity verification\n                    before you can start the proctored exam.\n                ": "\n                    Ihre Verifikation ist abgelaufen. Sie m\u00fcssen sich erneut erfolgreich verifizieren\n                    bevor Sie die beaufsichtigte Pr\u00fcfung beginnen k\u00f6nnen.\n                ", 
    "\n                    Your verification is pending. Results should be available 2-3 days after you\n                    submit your verification.\n                ": "\n                    Ihre Verifizierung in Bearbeitung. DIe Ergebnisse sollten 2-3 Tage\nnach Einreichung zur Verifikation verf\u00fcgbar sein.\n                ", 
    "\n                Complete your verification before starting the proctored exam.\n            ": "\n                Schlie\u00dfen Sie die Verifikation ab, bevor Sie mit der beaufsichtigten Pr\u00fcfung beginnen.\n            ", 
    "\n                You must successfully complete identity verification before you can start the proctored exam.\n            ": "\n                Sie m\u00fcssen die Verifikation Ihrer Identit\u00e4t vollst\u00e4ndig durchf\u00fchren, bevor Sie die beaufsichtigte Pr\u00fcfung beginnen k\u00f6nnen.\n            ", 
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\n            Schlie\u00dfen Sie nicht das Fenster, solange Sie die Pr\u00fcfung nicht abgeschlossen haben. Sollten Sie das Fenster trotzdem schli\u00dfen, ist Ihre Pr\u00fcfung beendet und wird nicht gewertet.\n          ", 
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\n            Zur\u00fcck zum %(platform_name)s Kurs, um die Pr\u00fcfung zu starten. Wenn Sie dieses beendet haben und\n            es als beendet markiert ist, k\u00f6nnen Sie das Fenster schlie\u00dfen, sodass die Session endet.\nAnschlie\u00dfend k\u00f6nnen Sie Ihre Daten zur Durchsicht hochladen.          ", 
    "\n          3. When you have finished setting up proctoring, start the exam.\n        ": "\n          3. Wenn Sie die Beaufsichtigungseinstellungen beendet haben, starten Sie mit der Pr\u00fcfung.\n        ", 
    "\n          Start my exam\n        ": "\n          Beginne mit meiner Pr\u00fcfung\n        ", 
    "\n        1. Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n      ": "\n        1. Kopieren Sie den Individuellen Pr\u00fcfungs-Code. Sie werden aufgefordert, diesen Code sp\u00e4ter einzuf\u00fcgen, bevor Sie mit der Pr\u00fcfung beginnen.\n      ", 
    "\n        2. Follow the link below to set up proctoring.\n      ": "\n        2. Folgen Sie dem Link unten, um die Beaufsichtigungeinzurichten.\n      ", 
    "\n        A new window will open. You will run a system check before downloading the proctoring application.\n      ": "\n        Ein neues Fenster wird sich \u00f6ffnen. Es wird ein System Kontrolle durchlaufen, bevor die Beaufsichtigungs-Applikation heruntergeladen wird.\n      ", 
    "\n        About Proctored Exams\n        ": "\n        \u00dcber Pr\u00fcfungen unter Aufsicht\n        ", 
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n        Sind Sie sicher, dass Sie an dieser Pr\u00fcfung ohne Aufsicht teilnehmen wollen?\n      ", 
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\n        Aufgrund von unerf\u00fcllten Voraussetzungen k\u00f6nnen Sie an dieser Pr\u00fcfung nur ohne Aufsicht teilnehmen.\n      ", 
    "\n        I am not interested in academic credit.\n      ": "\n        Ich bin nicht am Erwerb akademischer Kreditpunkte interessiert.\n      ", 
    "\n        I am ready to start this timed exam.\n      ": "\n        Ich bin bereit diese terminierte Pr\u00fcfung zu starten.\n      ", 
    "\n        If you take this exam without proctoring, you will <strong> no longer be eligible for academic credit. </strong>\n      ": "\n        Wenn Sie an dieser Pr\u00fcfung ohne Aufsicht teilnehmen, k\u00f6nnen Sie <strong>keine akademischen Kreditpunke erwerben. </strong>\n      ", 
    "\n        No, I want to continue working.\n      ": "\n        Nein, ich m\u00f6chte weiterarbeiten.\n      ", 
    "\n        No, I'd like to continue working\n      ": "\n        Nein, ich m\u00f6chte noch weiterarbeiten.\n      ", 
    "\n        Select the exam code, then copy it using Command+C (Mac) or Control+C (Windows).\n      ": "\n        W\u00e4hlen Sie einen Pr\u00fcfungs-Code und kopieren Sie diesen mit Command+C(Mac) oder Control+C(Windows).\n      ", 
    "\n        The time allotted for this exam has expired. Your exam has been submitted and any work you completed will be graded.\n      ": "\n        Die angesetzte Zeit f\u00fcr diese Pr\u00fcfung ist abgelaufen und Ihre Pr\u00fcfung wurde nun eingereicht. Nur die von Ihnen bearbeiteten Aufgaben werden Benotet\n      ", 
    "\n        You will be asked to verify your identity as part of the proctoring exam set up.\n        Make sure you are on a computer with a webcam, and that you have valid photo identification\n        such as a driver's license or passport, before you continue.\n      ": "\n        Im Rahmen der Beaufsichtigung werden Sie aufgefordert, sich zu identifizieren.\n        Stellen Sie sicher, dass Ihr Computer an einer funktionsf\u00e4higen Webcam angeschlossen ist und dass Sie einen validen Lichtbildausweis vorliegen haben.\n      Beispielsweise Personalausweis, F\u00fchrerschein, Reisepass, etc.", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.\n      ": "\n        Sie werden nun durch erforderliche Schritte gef\u00fchrt um die Online-Aufsichtssoftware aufzusetzen und eine Reihe von Tests und \u00dcberpr\u00fcfungen durchzuf\u00fchren.\n      ", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.</br>\n      ": "\n        Sie werden nun durch erforderliche Schritte gef\u00fchrt um die Online-Aufsichtssoftware aufzusetzen und eine Reihe von Tests und \u00dcberpr\u00fcfungen durchzuf\u00fchren.</br>\n      ", 
    "\n      A technical error has occurred with your proctored exam. To resolve this problem, contact\n      <a href=\"mailto:%(tech_support_email)s\">technical support</a>. All exam data, including answers\n      for completed problems, has been lost. When the problem is resolved you will need to restart\n      the exam and complete all problems again.\n    ": "\n      Es gab ein technisches Problem mit Ihrer beaufsichtigten Pr\u00fcfung. Um dieses Problem zu beseitigen wenden Sie sich an den\n      <a href=\"mailto:%(tech_support_email)s\">technischen Support</a>. Alle Pr\u00fcfungsdaten, auch Ihre Antworten\nf\u00fcr erledigte Aufgaben sind verloren gegangen. Wenn das Problem gel\u00f6st ist, m\u00fcssen Sie\ndie Pr\u00fcfung erneut starten und alle Aufgaben noch einmal l\u00f6sen.\n    ", 
    "\n      After you submit your exam, your exam will be graded.\n    ": "\n      Nachdem Einreichen Ihrer Pr\u00fcfung, folgt die Benotung.\n    ", 
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n      Sind Sie sicher, dass Sie Ihre terminierte Pr\u00fcfung einreichen m\u00f6chten?\n    ", 
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      Sind Sie sicher, dass sie Ihre beaufsichtigte Pr\u00fcfung beenden wollen?\n    ", 
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\n      Da das F\u00e4lligkeitsdatum \u00fcberschritten ist, k\u00f6nnen Sie an dieser Pr\u00fcfung nicht mehr teilnehmen.\n    ", 
    "\n      Error with proctored exam\n    ": "\nFehler mit der beaufsichtigten Pr\u00fcfung", 
    "\n      Follow these instructions\n    ": "\n      Befolgen Sie diese Anweisungen\n    ", 
    "\n      Follow these steps to set up and start your proctored exam.\n    ": "\n      Folgen Sie diesen Schritten um Ihre beaufsichtigte Pr\u00fcfung aufzusetzen und zu beginnen.\n    ", 
    "\n      Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n      on your grade in the course.\n    ": "\n      Machen Sie sich hier in diesem Kurs vertraut mit beaufsichtigten Pr\u00fcfungen um f\u00fcr sp\u00e4tere\nechte Pr\u00fcfungen bereit zu sein. Diese \u00dcbungspr\u00fcfung hat keinen Einfluss auf Ihre Noten in diesem Kurs.", 
    "\n      If you have concerns about your proctoring session results, contact your course team.\n    ": "\n      Falls Sie Bef\u00fcrchtungen bez\u00fcglich der Ergebnisse Ihrer beaufsichtigten Sitzung haben, nehmen Sie mit dem Kursteam Kontakt auf.\n    ", 
    "\n      If you have questions about the status of your requirements for course credit, contact %(platform_name)s Support.\n    ": "\n      Falls Sie fragen zum Fortschritt der Anforderungen ihrer Kurskreditpunke haben, kontaktieren Sie den %(platform_name)s Support.\n    ", 
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\n      Stellen Sie sicher, dass Sie jede Aufgabe  mit \"Abgabe\" markiert haben bevor Sie die Pr\u00fcfung beenden.\n    ", 
    "\n      Practice exams do not affect your grade or your credit eligibility.\n      You have completed this practice exam and can continue with your course work.\n    ": "\n      \u00dcbungspr\u00fcfungen beeinflussen Ihre Noten oder Ihre Kredit-Qualifikation nicht.\n      Sie m\u00fcssen diese \u00dcbungspr\u00fcfung absolvieren und k\u00f6nnen danach mit der Arbeit an Ihrem Kurs fortfahren.\n    ", 
    "\n      The due date for this exam has passed\n    ": "\nDas F\u00e4lligkeitsdatum f\u00fcr diese Pr\u00fcfung ist \u00fcberschritten.", 
    "\n      There was a problem with your practice proctoring session\n    ": "\n      Es gab ein Problem mit Ihrer \u00dcbungssitzung unter Aufsicht", 
    "\n      This exam is proctored\n    ": "\nDiese Pr\u00fcfung geschieht unter Aufsicht", 
    "\n      To be eligible for course credit or for a MicroMasters credential, you must pass the proctoring review for this exam.\n    ": "\nUm f\u00fcr Kurs-Kreditpunkte oder MicroMaster Credentials berechtigt zu sein, m\u00fcssen Sie den beaufsichtigten Review f\u00fcr diese Pr\u00fcfung bestehen.", 
    "\n      Try a proctored exam\n    ": "\n      Starte eine Betreute Pr\u00fcfung\n    ", 
    "\n      View your credit eligibility status on your <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\n      Sehen Sie den Status ihrer Kredit-Qualifikation auf Ihrer <a href=\"%(progress_page_url)s\">Fortschritt</a>-Seite.\n    ", 
    "\n      Yes, end my proctored exam\n    ": "\n      Ja, beaufsichtigung jetzt beenden.\n    ", 
    "\n      Yes, submit my timed exam.\n    ": "\n     Ja, meine terminierte Pr\u00fcfung jetzt einreichen.\n    ", 
    "\n      You have submitted this practice proctored exam\n    ": "\n      Sie haben diese beaufsichtigte \u00dcbungspr\u00fcfung eingereicht\n    ", 
    "\n      You have submitted this proctored exam for review\n    ": "\n      Sie haben diese beaufsichtigte Pr\u00fcfung zur Durchsicht hochgeladen.\n    ", 
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\n      Ergebnisse Ihrer \u00dcbungsaufsicht: <b class=\"failure\"> Nicht ausreichend </b>\n    ", 
    "\n      Your proctoring session ended before you completed this practice exam.\n      You can retry this practice exam if you had problems setting up the online proctoring software.\n    ": "\n      Ihre beaufsichtigte Sitzung endete bevor Sie diese \u00dcbungspr\u00fcfung abgeschossen haben.\n      Sie k\u00f6nnen diese \u00dcbungspr\u00fcfung wiederholen falls Sie Probleme hatten die Online-Aufsichtssoftware einrichten.\n    ", 
    "\n      Your proctoring session was reviewed and did not pass requirements\n    ": "\n      Ihre Beaufsichtigung wurde durchgesehen und nicht zugelassen.\n    ", 
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n    %(exam_name)s ist eine terminierte Pr\u00fcfung (%(total_time)s)\n    ", 
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\n   Die folgenden Voraussetzungen sind in einem <strong>unvollst\u00e4ndigen</strong> Status und m\u00fcssen erfolgreich abgeschlossen sein bevor Sie starten k\u00f6nnen.\n    ", 
    "\n    You can take this exam with proctoring only when all prerequisites have been successfully completed. Check your <a href=\"%(progress_page_url)s\">Progress</a>  page to see if prerequisite results have been updated. You can also take this exam now without proctoring, but you will not be eligible for credit.\n    ": "\n   Sie k\u00f6nnen diese Pr\u00fcfung nur starten, wenn alle Anforderungen erfolgreich abgeschlossen sind. Kontrollieren Sie Ihren <a href=\"%(progress_page_url)s\">Kursfortschritt</a>, um zu sehen ob dies der Fall ist. Sie k\u00f6nnen diese Pr\u00fcfung dennoch starten, jedoch ohne Beaufsichtigung und ohne sp\u00e4teren Credit. \n    ", 
    "\n    You did not satisfy the following prerequisites:\n    ": "\n    Sie erf\u00fcllen die folgenden Vorraussetzungen nicht:\n    ", 
    "\n    You did not satisfy the requirements for taking this exam with proctoring, and are not eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements and your status for each.\n    ": "\n    Sie erf\u00fcllen die Vorbedingungen f\u00fcr diese beaufsichtigte Pr\u00fcfung nicht. Auch haben Sie die Qualifikation f\u00fcr Kreditpunkte nicht. Ihre <a href=\"%(progress_page_url)s\">Fortschritt</a>-Seite enth\u00e4lt eine Liste der Vorbedingungen und Ihren Status f\u00fcr jede einzelne.\n    ", 
    "\n    You have not completed the prerequisites for this exam. All requirements must be satisfied before you can take this proctored exam and be eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements in the order that they must be completed.\n    ": "\n   Sie haben die Voraussetzungen f\u00fcr diese Pr\u00fcfung. Alle Anforderungen m\u00fcssen befriedigend sein, bevor Sie diese beaufsichtigte Pr\u00fcfung machen k\u00f6nnen und einen Credit daf\u00fcr erhlten. Schauen Sie sich Ihren <a href=\"%(progress_page_url)s\">Kursfortschritt</a> an, um zu kontrollieren, ob Sie alle Anforderungen bestehen. \n    ", 
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": " Von jetzt an m\u00fcssen Sie den <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online Beaufsichtigungsregeln</a> folgen, um damit Ihre Pr\u00fcfung zugelassen wird.", 
    " Your Proctoring Session Has Started ": "Ihre beaufsichtigte Sitzung hat begonnen", 
    " and {num_of_minutes} minutes": " und {num_of_minutes} Minuten", 
    " to complete and submit the exam.": "Zum Beenden und Einreichen der Pr\u00fcfung.", 
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s von %(cnt)s ausgew\u00e4hlt", 
      "%(sel)s von %(cnt)s ausgew\u00e4hlt"
    ], 
    "(required):": "(erforderlich):", 
    "6 a.m.": "6 Uhr", 
    "6 p.m.": "18 Uhr", 
    "Additional Time (minutes)": "Zus\u00e4tzliche Zeit (Minuten)", 
    "After you select ": "Nach Ihrer Auswahl", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Wenn Sie neue Dateien hochladen, werden die zuvor hochgeladenen Dateien \u00fcberschrieben. M\u00f6chten Sie dennoch fortfahren?", 
    "All Unreviewed": "Alle mit fehlendem Review", 
    "All Unreviewed Failures": "Alle nicht Bestandenen mit fehlendem Review", 
    "April": "April", 
    "Assessment": "Beurteilung", 
    "Assessments": "Beurteilungen", 
    "August": "August", 
    "Available %s": "Verf\u00fcgbare %s", 
    "Back to Full List": "Zur\u00fcck zur kompletten Liste", 
    "Block view is unavailable": "Blockansicht ist nicht verf\u00fcgbar", 
    "Cancel": "Abbrechen", 
    "Cannot Start Proctored Exam": "Beaufsichtigte Pr\u00fcfung kann nicht begonnen werden", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "\u00c4nderungen an Schritten, die nicht als Teil der Aufgabe ausgew\u00e4hlt sind, werden nicht gespeichert.", 
    "Choose": "Ausw\u00e4hlen", 
    "Choose a Date": "Datum w\u00e4hlen", 
    "Choose a Time": "Uhrzeit w\u00e4hlen", 
    "Choose a time": "Uhrzeit", 
    "Choose all": "Alle ausw\u00e4hlen", 
    "Chosen %s": "Ausgew\u00e4hlte %s", 
    "Click to choose all %s at once.": "Klicken, um alle %s auf einmal auszuw\u00e4hlen.", 
    "Click to remove all chosen %s at once.": "Klicken, um alle ausgew\u00e4hlten %s auf einmal zu entfernen.", 
    "Close": "Schlie\u00dfen", 
    "Continue Exam Without Proctoring": "Diese Pr\u00fcfung ohne Aufsicht fortsetzen", 
    "Continue to Verification": "Weiter zur Verifikation", 
    "Continue to my practice exam": "Weiter zu meiner \u00dcbungspr\u00fcfung", 
    "Continue to my proctored exam. I want to be eligible for credit.": "Weiter zu meiner beaufsichtigten Pr\u00fcfung. Ich m\u00f6chte zu Kreditpunkten berechtigt sein.", 
    "Could not retrieve download url.": "Die Download URL konnte nicht aufgefunden werden.", 
    "Could not retrieve upload url.": "Die Upload-URL konnte nicht aufgefunden werden.", 
    "Couldn't Save This Assignment": "Konnte diese Aufgabe nicht speichern", 
    "Course Id": "Kurs ID", 
    "Created": "Erstellt", 
    "Criterion Added": "Kriterium hinzugef\u00fcgt", 
    "Criterion Deleted": "Kriterium gel\u00f6scht", 
    "December": "Dezember", 
    "Declined": "Abgelehnt", 
    "Describe ": "Beschreibe", 
    "Do you want to upload your file before submitting?": "M\u00f6chten Sie die Datei hochladen, bevor Sie Ihre Antwort einreichen?", 
    "Doing so means that you are no longer eligible for academic credit.": "Die Konsequenz hieraus ist, dass Sie nicht l\u00e4nger zum Erwerb akademische Kreditpunkte berechtigt sind.", 
    "Download Software Clicked": "Software Download gew\u00e4hlt", 
    "Error": "Fehler", 
    "Error getting the number of ungraded responses": "Fehler bei der Abfrage der Anzahl der unbenoteten Antworten", 
    "Failed Proctoring": "Nicht bestanden unter Beaufsichtigung", 
    "February": "Februar", 
    "Feedback available for selection.": "Feedback f\u00fcr die Auswahl verf\u00fcgbar.", 
    "File size must be 10MB or less.": "Datei darf maximal 10MB gro\u00df sein.", 
    "File type is not allowed.": "Dieser Dateityp ist nicht erlaubt. ", 
    "File types can not be empty.": "Dateityp darf nicht leer sein.", 
    "Filter": "Filter", 
    "Final Grade Received": "Erhaltene Endnote", 
    "Go Back": "Gehe zur\u00fcck", 
    "Heading 3": "\u00dcberschrift 3", 
    "Heading 4": "\u00dcberschrift 4", 
    "Heading 5": "\u00dcberschrift 5", 
    "Heading 6": "\u00dcberschrift 6", 
    "Hide": "Ausblenden", 
    "I am ready to start this timed exam,": "Ich bin bereit diese zeitlich begrenzte Pr\u00fcfung zu beginnen, ", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Wenn Sie diese Seite ohne vorheriges Speichern oder Einreichen der Antwort verlassen, geht die Arbeit an dieser Antwort verloren.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Wenn Sie diese Seite verlassen ohne Ihre Partnerbewertung zu \u00fcbermitteln, werden Sie alle Ihre bis jetzt erledigte Arbeit verlieren.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Wenn Sie diese Seite ohne vorheriges Speichern oder Einreichen der Antwort verlassen, geht die Arbeit an dieser Antwort verloren.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Wenn Sie diese Seite ohne Einreichung der Mitarbeiterbewertung verlassen, geht Ihre Arbeit verloren.", 
    "Is Sample Attempt": "Ist ein Probeversuch", 
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
    "Passed Proctoring": "Bestanden unter Beaufsichtigung", 
    "Peer": "Partner", 
    "Pending Session Review": "Laufende Begutachtung der Sitzung", 
    "Please correct the outlined fields.": "Bitte korrigiere die umrandeten Felder.", 
    "Please wait": "Bitte warten", 
    "Practice Exam Completed": "\u00dcbungspr\u00fcfung bestanden", 
    "Practice Exam Failed": "\u00dcbungspr\u00fcfung nicht bestanden", 
    "Preformatted": "Vorformatiert", 
    "Proctored Option Available": "Option Beaufsichtigt verf\u00fcgbar", 
    "Proctored Option No Longer Available": "Die Option Beaufsichtigt steht nicht l\u00e4nger zur Verf\u00fcgung", 
    "Proctoring Session Results Update for {course_name} {exam_name}": "Aktualisierung der beaufsichtigten Sitzungsergebnisse f\u00fcr {course_name} {exam_name}", 
    "Ready To Start": "Bereit um zu starten", 
    "Ready To Submit": "Bereit f\u00fcr die Einreichung", 
    "Rejected": "Zur\u00fcckgewiesen", 
    "Remove": "Entfernen", 
    "Remove all": "Alle entfernen", 
    "Retry Verification": "Verifikation wiederholen", 
    "Review Policy Exception": "Ausnahme bei der Begutachtungsrichtlinine", 
    "Saving...": "Speichert...", 
    "Second Review Required": "Zweiter Review wird ben\u00f6tigt", 
    "Self": "Selbst", 
    "September": "September", 
    "Server error.": "Server Problem.", 
    "Show": "Einblenden", 
    "Staff": "Betreuung", 
    "Start Proctored Exam": "Beaufsichtigte Pr\u00fcfung beginnen", 
    "Start System Check": "Beginne mit Systemcheck", 
    "Started": "Gestartet", 
    "Status of Your Response": "Status Ihrer Antwort", 
    "Submitted": "Abgesendet", 
    "Take this exam without proctoring.": "An diese Pr\u00fcfung ohne Aufsicht teilnehmen.", 
    "Taking As Open Exam": "Als eine Freie Pr\u00fcfung teilnehmen", 
    "Taking As Proctored Exam": "Als eine beaufsichtigten Pr\u00fcfung teilnehmen", 
    "Taking as Proctored": "Als Beaufsichtigt teilnehmen", 
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
    "Timed Exam": "Terminierte Pr\u00fcfung", 
    "Timed Out": "Timed Out", 
    "Today": "Heute", 
    "Tomorrow": "Morgen", 
    "Total Responses": "Gesamte Anzahl Antworten", 
    "Training": "Training", 
    "Try this practice exam again": "Diese \u00dcbungspr\u00fcfung noch einmal versuchen", 
    "Type into this box to filter down the list of available %s.": "Durch Eingabe in diesem Feld l\u00e4sst sich die Liste der verf\u00fcgbaren %s eingrenzen.", 
    "Unable to load": "Laden nicht m\u00f6glich", 
    "Unexpected server error.": "Ein unerwarteter Fehler ist aufgetreten.", 
    "Ungraded Practice Exam": "Upgrade auf Praktische Pr\u00fcfung", 
    "Unit Name": "Name der Lerneinheit", 
    "Units": "Lerneinheiten", 
    "Unnamed Option": "Unbenannte Option", 
    "Verified": "Gepr\u00fcft", 
    "View my exam": "Meine Pr\u00fcfung anzeigen", 
    "Waiting": "Warten", 
    "Warning": "Warnung", 
    "Yesterday": "Gestern", 
    "You can also retry this practice exam": "Sie k\u00f6nnen diese \u00dcbungspr\u00fcfung auch noch einmal versuchen", 
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
    "active proctored exams": "aktiv betreute Pr\u00fcfungen", 
    "could not determine the course_id": "Konnte course_id nicht feststellen", 
    "courses with active proctored exams": "Kurse mit aktiv betreuten Pr\u00fcfungen", 
    "internally reviewed": "Intern begutachtet / reviewed", 
    "one letter Friday\u0004F": "Fr", 
    "one letter Monday\u0004M": "Mo", 
    "one letter Saturday\u0004S": "Sa", 
    "one letter Sunday\u0004S": "So", 
    "one letter Thursday\u0004T": "Do", 
    "one letter Tuesday\u0004T": "Di", 
    "one letter Wednesday\u0004W": "Mi", 
    "pending": "ausstehend", 
    "satisfactory": "ausreichend", 
    "timed": "Terminiert", 
    "unsatisfactory": "ungen\u00fcgend", 
    "you will have ": "Sie haben in Zukunft", 
    "your course": "Ihr Kurs", 
    "{num_of_hours} hour": "{num_of_hours} Stunde", 
    "{num_of_hours} hours": "{num_of_hours} Stunden"
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

