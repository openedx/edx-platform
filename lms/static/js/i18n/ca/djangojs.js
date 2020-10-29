

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
    "\n\nThis email is to let you know that the status of your proctoring session review for %(exam_name)s in\n<a href=\"%(course_url)s\">%(course_name)s </a> is %(status)s. If you have any questions about proctoring,\ncontact %(platform)s support at %(contact_email)s.\n\n": "\n\nAquest correu electr\u00f2nic us permet fer-vos saber que l'estat de la revisi\u00f3 de la vostra sessi\u00f3 de supervisi\u00f3 correspon a %(exam_name)s a\n<a href=\"%(course_url)s\">%(course_name)s </a> est\u00e0 %(status)s. Si teniu cap pregunta sobre la supervisi\u00f3,\ncontacteu %(platform)s amb el suport a %(contact_email)s.\n\n", 
    "\n                    Make sure you are on a computer with a webcam, and that you have valid photo identification\n                    such as a driver's license or passport, before you continue.\n                ": "\n                    Assegureu-vos que sou en una computadora amb una c\u00e0mera web i que tingueu una identificaci\u00f3 amb foto v\u00e0lida\n                    com ara una llic\u00e8ncia de conduir o un passaport, abans de continuar.\n                ", 
    "\n                    Your verification attempt failed. Please read our guidelines to make\n                    sure you understand the requirements for successfully completing verification,\n                    then try again.\n                ": "\n                    Ha fallat l'intent de verificaci\u00f3. Llegiu les nostres directrius per\n                    assegurar-vos d'entendre els requisits per completar la verificaci\u00f3 amb \u00e8xit,\n                    torneu-ho a provar.\n                ", 
    "\n                    Your verification has expired. You must successfully complete a new identity verification\n                    before you can start the proctored exam.\n                ": "\n                    La teva verificaci\u00f3 ha caducat. Heu de completar amb \u00e8xit una nova verificaci\u00f3 d'identitat\n                    abans de poder iniciar l'examen supervisat.\n                ", 
    "\n                    Your verification is pending. Results should be available 2-3 days after you\n                    submit your verification.\n                ": "\n                    La verificaci\u00f3 est\u00e0 pendent. Els resultats haurien d'estar disponibles 2 o 3 dies despr\u00e9s d'haver-los fet\n                    envieu la vostra verificaci\u00f3.\n                ", 
    "\n                Complete your verification before starting the proctored exam.\n            ": "\n                Completeu la vostra verificaci\u00f3 abans d'iniciar l'examen processat.\n            ", 
    "\n                You must successfully complete identity verification before you can start the proctored exam.\n            ": "\n                Cal completar amb \u00e8xit la verificaci\u00f3 d'identitat abans de poder iniciar l'examen supervisat.\n            ", 
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\n            No tanqueu aquesta finestra abans d'acabar l'examen. si tanqueu aquesta finestra, la vostra sessi\u00f3 de processament finalitza i no finalitzar\u00e0 amb \u00e8xit l'examen processat.\n          ", 
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\n            Torneu a la finestra del curs %(platform_name)s per comen\u00e7ar l'examen. Quan hagueu acabat l'examen i\n            ho heu marcat com a complet, podeu tancar aquesta finestra per finalitzar la sessi\u00f3 de processament\n            i carregueu les dades de la sessi\u00f3 de supervisi\u00f3 per a la seva revisi\u00f3.\n          ", 
    "\n          3. When you have finished setting up proctoring, start the exam.\n        ": "\n          3. Quan h\u00e0giu acabat de configurar la supervisi\u00f3 pr\u00e8via, comenceu l'examen.\n        ", 
    "\n          Start my exam\n        ": "\n          Comen\u00e7a el meu examen\n        ", 
    "\n        &#8226; When you start your exam you will have %(total_time)s to complete it. </br>\n        &#8226; You cannot stop the timer once you start. </br>\n        &#8226; If time expires before you finish your exam, your completed answers will be\n                submitted for review. </br>\n      ": "\n        &#8226; Quan inicieu l'examen que tindreu %(total_time)s que completar-ho. </br>\n        &#8226; No podeu parar el rellotge un cop he comen\u00e7at. </br>\n        &#8226; Si el temps caduca abans d'acabar l'examen, les seves respostes completes seran\n                presentades per a la seva revisi\u00f3.</br>\n      ", 
    "\n        1. Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n      ": "\n        1. Copieu aquest codi d'examen \u00fanic. Se us demanar\u00e0 que enganxeu aquest codi m\u00e9s endavant abans d'iniciar l'examen.\n      ", 
    "\n        2. Follow the link below to set up proctoring.\n      ": "\n        2. Seguiu l'enlla\u00e7 seg\u00fcent per configurar la supervisi\u00f3.\n      ", 
    "\n        A new window will open. You will run a system check before downloading the proctoring application.\n      ": "\n        S'obrir\u00e0 una finestra nova. Realitzar\u00e0s una verificaci\u00f3 del sistema abans de descarregar l'aplicaci\u00f3 de tramitaci\u00f3.\n      ", 
    "\n        About Proctored Exams\n        ": "\n        Al voltant de Ex\u00e0mens Supervisats\n        ", 
    "\n        After the due date has passed, you can review the exam, but you cannot change your answers.\n      ": "\n        Despr\u00e9s de la data de venciment, podeu revisar l'examen, per\u00f2 no podeu canviar les vostres respostes.\n      ", 
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n        Esteu segur que voleu fer aquest examen sense fer proves?\n      ", 
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\n        A causa de requisits previs insatisfets, nom\u00e9s podeu fer aquest examen sense fer proves.\n      ", 
    "\n        I am not interested in academic credit.\n      ": "\n        No m'interessa el cr\u00e8dit acad\u00e8mic.\n      ", 
    "\n        I am ready to start this timed exam.\n      ": "\n        Estic preparat per iniciar aquest examen cronometrat.\n      ", 
    "\n        If you take this exam without proctoring, you will <strong> no longer be eligible for academic credit. </strong>\n      ": "\n        Si feu aquest examen sense processament, no ser\u00e0 <strong> elegible per al cr\u00e8dit acad\u00e8mic.</strong>\n      ", 
    "\n        No, I want to continue working.\n      ": "\n        No, vull seguir treballant.\n      ", 
    "\n        No, I'd like to continue working\n      ": "\n        No, m'agradaria continuar treballant\n      ", 
    "\n        Select the exam code, then copy it using Command+C (Mac) or Control+C (Windows).\n      ": "\n        Seleccioneu el codi de l'examen i, a continuaci\u00f3, copieu-lo usant Command + C (Mac) o Control + C (Windows).\n      ", 
    "\n        The time allotted for this exam has expired. Your exam has been submitted and any work you completed will be graded.\n      ": "\n        El temps assignat per a aquest examen ha caducat. S'ha enviat el vostre examen i es classificar\u00e0 el treball completat.\n      ", 
    "\n        You have submitted your timed exam.\n      ": "\n        Heu enviat el vostre examen cronometrat.\n      ", 
    "\n        You will be asked to verify your identity as part of the proctoring exam set up.\n        Make sure you are on a computer with a webcam, and that you have valid photo identification\n        such as a driver's license or passport, before you continue.\n      ": "\n        Se us demanar\u00e0 que verifiqueu la vostra identitat com a part de la configuraci\u00f3 de l'examen de supervisi\u00f3.\n        Assegureu-vos que sou en una computadora amb una c\u00e0mera web i que tingueu una identificaci\u00f3 amb foto v\u00e0lida\n        com ara una llic\u00e8ncia de conduir o un passaport, abans de continuar.\n      ", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.\n      ": "\n        Us guiarem pels passos necessaris per configurar el programari de processament en l\u00ednia i realitzar diversos controls.\n      ", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.</br>\n      ": "\n       Us guiarem pels passos necessaris per configurar el programari de processament en l\u00ednia i realitzar diversos controls.</br>\n      ", 
    "\n      &#8226; After you quit the proctoring session, the recorded data is uploaded for review. </br>\n      &#8226; Proctoring results are usually available within 5 business days after you submit your exam.\n    ": "\n      &#8226; Despr\u00e9s d'abandonar la sessi\u00f3 de supervisi\u00f3, es carregaran les dades gravades per a la seva revisi\u00f3. </br>\n      &#8226; Els resultats de la supervisi\u00f3 solen estar disponibles dins dels 5 dies h\u00e0bils posteriors a l'enviament de l'examen.\n    ", 
    "\n      A technical error has occurred with your proctored exam. To resolve this problem, contact\n      <a href=\"mailto:%(tech_support_email)s\">technical support</a>. All exam data, including answers\n      for completed problems, has been lost. When the problem is resolved you will need to restart\n      the exam and complete all problems again.\n    ": "\n      S'ha produ\u00eft un error t\u00e8cnic amb l'examen supervisat. Per resoldre aquest problema, poseu-vos en contacte amb\n      <a href=\"mailto:%(tech_support_email)s\"> el suport t\u00e8cnic</a>. Totes les dades de l'examen, incloses les respostes\n      per problemes complets, s'ha perdut. Quan es resol el problema, haur\u00e0s de reiniciar\n      l'ex\u00e0men icompletar els problemes de nou.\n    ", 
    "\n      After the due date for this exam has passed, you will be able to review your answers on this page.\n    ": "\n      Un cop superada la data de venciment d'aquest examen, podreu revisar les vostres respostes en aquesta p\u00e0gina.\n    ", 
    "\n      After you submit your exam, your exam will be graded.\n    ": "\n     Despr\u00e9s d'enviar el vostre examen, el vostre examen es classificar\u00e0.\n    ", 
    "\n      After you submit your exam, your responses are graded and your proctoring session is reviewed.\n      You might be eligible to earn academic credit for this course if you complete all required exams\n      as well as achieve a final grade that meets credit requirements for the course.\n    ": "\n      Despr\u00e9s d'enviar l'examen, les seves respostes es classifiquen i es revisa la seva sessi\u00f3 de supervisi\u00f3.\n      Podria ser elegible per obtenir el cr\u00e8dit acad\u00e8mic d'aquest curs si completa tots els ex\u00e0mens requerits\n      aix\u00ed com aconseguir una nota final que compleixi els requisits de cr\u00e8dit del curs.\n    ", 
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n      Est\u00e0s segur que vols enviar el teu examen cronol\u00f2gic?\n    ", 
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      Esteu segur que voleu finalitzar el vostre examen supervisat?\n    ", 
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\n      Com que ja ha passat la data de venciment, ja no podreu fer aquest examen.\n    ", 
    "\n      Error with proctored exam\n    ": "\n      S'ha produ\u00eft un error en l'examen supervisat\n    ", 
    "\n      Follow these instructions\n    ": "\n      Seguiu aquestes instruccions\n    ", 
    "\n      Follow these steps to set up and start your proctored exam.\n    ": "\n     Seguiu aquests passos per configurar i iniciar l'examen supervisat.\n    ", 
    "\n      Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n      on your grade in the course.\n    ": "\n      Familiaritzeu-vos amb la preparaci\u00f3 d'ex\u00e0mens reals m\u00e9s tard en el curs. Aquest examen de pr\u00e0ctica no t\u00e9 cap impacte\n      a la vostra nota del curs.\n    ", 
    "\n      If the proctoring software window is still open, you can close it now. Confirm that you want to quit the application when you are prompted.\n    ": "\n     Si la finestra del programari de processament encara est\u00e0 oberta, ara podeu tancar-la ara. Confirmeu que voleu deixar l'aplicaci\u00f3 quan se us demani.\n    ", 
    "\n      If you have concerns about your proctoring session results, contact your course team.\n    ": "\n      Si teniu dubtes sobre els resultats de la sessi\u00f3 de supervisi\u00f3, contacteu amb l'equip del vostre curs.\n    ", 
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\n     Si teniu discapacitats,\n      \u00e9s possible que tingueu dret a una assignaci\u00f3 de temps addicional en ex\u00e0mens temporitzats.\n      Pregunteu a l'equip del vostre curs per obtenir informaci\u00f3 sobre les assignacions de temps addicionals.", 
    "\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\n     Si teniu preguntes sobre l'estat dels resultats dels ex\u00e0mens supervisats, contacteu amb el suport de %(platform_name)s.\n    ", 
    "\n      If you have questions about the status of your requirements for course credit, contact %(platform_name)s Support.\n    ": "\n     Si teniu preguntes sobre l'estat dels vostres requisits per al cr\u00e8dit del curs, contacteu amb el suport de   %(platform_name)s \n    ", 
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\n      Assegureu-vos que heu seleccionat \"Enviar\" per a cada problema abans d'enviar l'examen.\n    ", 
    "\n      Practice exams do not affect your grade or your credit eligibility.\n      You have completed this practice exam and can continue with your course work.\n    ": "\n      Els ex\u00e0mens pr\u00e0ctics no afecten el vostre grau o la vostra elegibilitat credit\u00edcia.\n      Heu completat aquest examen de pr\u00e0ctica i podeu continuar amb el vostre curs.\n    ", 
    "\n      The due date for this exam has passed\n    ": "\n      La data de venciment d'aquest examen ha passat\n    ", 
    "\n      There was a problem with your practice proctoring session\n    ": "\n      Hi ha hagut un problema amb la vostra sessi\u00f3 de supervisi\u00f3 de pr\u00e0ctiques\n    ", 
    "\n      This exam is proctored\n    ": "\n      Aquest ex\u00e0men est\u00e0 supervisat\n    ", 
    "\n      To be eligible for course credit or for a MicroMasters credential, you must pass the proctoring review for this exam.\n    ": "\n      Per poder optar al cr\u00e8dit del curs o per obtenir una credencial de MicroMasters, haureu de passar la revisi\u00f3 de supervisi\u00f3 per a aquest examen.\n    ", 
    "\n      To view your exam questions and responses, select <strong>View my exam</strong>. The exam's review status is shown in the left navigation pane.\n    ": "\n      Per veure les preguntes i respostes de l'examen, seleccioneu <strong>Veure el meu examen </strong>. L'estat de la revisi\u00f3 de l'examen es mostra al panell de navegaci\u00f3 esquerre.\n    ", 
    "\n      Try a proctored exam\n    ": "\n      Proveu un examen supervisat\n    ", 
    "\n      View your credit eligibility status on your <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\n      Consulteu el vostre estat d'elegibilitat de cr\u00e8dit a la vostre p\u00e0gina de  <a href=\"%(progress_page_url)s\">Progr\u00e9s</a> .\n    ", 
    "\n      Yes, end my proctored exam\n    ": "\n      S\u00ed, finalitzar el meu examen supervisat \n    ", 
    "\n      Yes, submit my timed exam.\n    ": "\n      S\u00ed, envieu el meu examen cronometrat.\n    ", 
    "\n      You are eligible to purchase academic credit for this course if you complete all required exams\n      and also achieve a final grade that meets the credit requirements for the course.\n    ": "\n      Podeu adquirir un cr\u00e8dit acad\u00e8mic per a aquest curs si completa els ex\u00e0mens requerits\n     i tamb\u00e9 aconseguir una nota final que compleixi amb els requisits de cr\u00e8dit del curs.\n    ", 
    "\n      You are no longer eligible for academic credit for this course, regardless of your final grade.\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\n     Ja no podeu obtenir cr\u00e8dits acad\u00e8mics per a aquest curs, independentment de la nota final.\n      Si teniu preguntes sobre l'estat dels resultats dels ex\u00e0mens supervisats, contacteu amb el suport de %(platform_name)s.\n    ", 
    "\n      You have submitted this practice proctored exam\n    ": "\n      Heu enviat aquest examen pr\u00e0ctic tutelat\n    ", 
    "\n      You have submitted this proctored exam for review\n    ": "\n      Heu enviat aquest examen tutelat per a la seva revisi\u00f3\n    ", 
    "\n      Your grade for this timed exam will be immediately available on the <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\n      El vostre grau d'aquest examen temporal estar\u00e0 disponible immediatament a la p\u00e0gina de <a href=\"%(progress_page_url)s\">Progr\u00e9s</a>.\n    ", 
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\n      Els resultats de la seva pr\u00e0ctica de supervisi\u00f3: <b class=\"failure\"> Insatisfactori </b>\n    ", 
    "\n      Your proctoring session ended before you completed this practice exam.\n      You can retry this practice exam if you had problems setting up the online proctoring software.\n    ": "\n      La sessi\u00f3 de supervisi\u00f3 finalitzava abans de completar aquest examen de pr\u00e0ctica.\n      Podeu tornar a provar aquest examen de pr\u00e0ctica si teniu problemes per configurar el programari de processament en l\u00ednia.\n    ", 
    "\n      Your proctoring session was reviewed and did not pass requirements\n    ": "\n      S'ha revisat la vostra sessi\u00f3 de supervisi\u00f3 i no va passar els requisits\n    ", 
    "\n      Your proctoring session was reviewed and passed all requirements\n    ": "\n      S'ha revisat la vostra sessi\u00f3 de supervisi\u00f3 i es van aprovar tots els requisits\n    ", 
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n    %(exam_name)s \u00e9s un examen cronometrat (%(total_time)s)\n    ", 
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\n    Els prerequisits seg\u00fcents es troben en estat <strong>pedent</strong> i s'ha de completar amb \u00e8xit abans de poder continuar:\n    ", 
    "\n    You can take this exam with proctoring only when all prerequisites have been successfully completed. Check your <a href=\"%(progress_page_url)s\">Progress</a>  page to see if prerequisite results have been updated. You can also take this exam now without proctoring, but you will not be eligible for credit.\n    ": "\n    Podeu fer aquest examen amb la supervisi\u00f3 nom\u00e9s quan tots els requisits previs s'han completat correctament. Consulteu la vostra p\u00e0gina de <a href=\"%(progress_page_url)s\">Progr\u00e9s</a>  per veure si s'han actualitzat els resultats previs. Tamb\u00e9 podeu fer aquest examen ara sense procedir, per\u00f2 no podreu obtenir el cr\u00e8dit.\n    ", 
    "\n    You did not satisfy the following prerequisites:\n    ": "\n    No heu satisfet els requisits previs seg\u00fcents:\n    ", 
    "\n    You did not satisfy the requirements for taking this exam with proctoring, and are not eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements and your status for each.\n    ": "\n    No heu satisfet els requisits per fer aquest examen amb supervisi\u00f3 pr\u00e8via, i no \u00e9s apte per al cr\u00e8dit. Mireu la vostra p\u00e0gina de  <a href=\"%(progress_page_url)s\">Progr\u00e9s</a> per obtenir una llista de requisits i el vostre estat per a cadascun.\n    ", 
    "\n    You have not completed the prerequisites for this exam. All requirements must be satisfied before you can take this proctored exam and be eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements in the order that they must be completed.\n    ": "\n    No heu completat els requisits previs per a aquest examen. Tots els requisits han de ser satisfets abans de poder fer aquest examen de prova i ser elegibles per al cr\u00e8dit. Mireu la vostra p\u00e0gina de <a href=\"%(progress_page_url)s\">Progr\u00e9s</a> per obtenir una llista de requisits en l'ordre que s'han de completar.\n    ", 
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": " A partir d 'aquest moment, heu de seguir les <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">regles de supervisi\u00f3 en l\u00ednia </a> Per aprovar la revisi\u00f3 de supervisi\u00f3 per al vostre examen.", 
    " Your Proctoring Session Has Started ": "S'ha iniciat la vostra sessi\u00f3 de supervisi\u00f3", 
    " and {num_of_minutes} minute": "i {num_of_minutes} minut", 
    " and {num_of_minutes} minutes": "i {num_of_minutes} minuts", 
    " to complete and submit the exam.": "per completar i enviar l'examen.", 
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s seleccionat", 
      "%(sel)s of %(cnt)s seleccionats"
    ], 
    "6 a.m.": "6 a.m.", 
    "6 p.m.": "6 p.m.", 
    "Additional Time (minutes)": "Temps addicional (minuts)", 
    "After you select ": "Despr\u00e9s de seleccionar", 
    "All Unreviewed": "Tots sense veure", 
    "All Unreviewed Failures": "Tots els errors no vistos", 
    "April": "Abril", 
    "August": "Agost", 
    "Available %s": "%s Disponibles", 
    "Can I request additional time to complete my exam?": "Puc demanar m\u00e9s temps per completar el meu examen?", 
    "Cancel": "Cancel\u00b7lar", 
    "Cannot Start Proctored Exam": "No es pot iniciar l'examen supervisat", 
    "Choose": "Escollir", 
    "Choose a Date": "Escolliu una data", 
    "Choose a Time": "Escolliu una hora", 
    "Choose a time": "Escolliu una hora", 
    "Choose all": "Escollir-los tots", 
    "Chosen %s": "Escollit %s", 
    "Click to choose all %s at once.": "Feu clic per escollir tots els %s d'un cop.", 
    "Click to remove all chosen %s at once.": "Feu clic per eliminar tots els %s escollits d'un cop.", 
    "Close": "Tancar", 
    "Continue Exam Without Proctoring": "Continua l'examen sense supervisi\u00f3", 
    "Continue to Verification": "Continueu a la verificaci\u00f3", 
    "Continue to my practice exam": "Continueu al meu examen de pr\u00e0ctica", 
    "Continue to my proctored exam. I want to be eligible for credit.": "Continueu al meu examen tutelat. Vull ser elegible per al cr\u00e8dit.", 
    "Course Id": "Identificador del Curs", 
    "Created": "Creat", 
    "December": "Desembre", 
    "Declined": "Rebutjat", 
    "Doing so means that you are no longer eligible for academic credit.": "Fer-ho significa que ja no \u00e9s apte per al cr\u00e8dit acad\u00e8mic.", 
    "Download Software Clicked": "Descarregueu el programari clicat", 
    "Error": "Error", 
    "Failed Proctoring": "Supervisat susp\u00e8s", 
    "February": "Febrer", 
    "Filter": "Filtre", 
    "Go Back": "Torna", 
    "Hide": "Ocultar", 
    "I am ready to start this timed exam,": "Estic preparat per iniciar aquest examen cronometrat,", 
    "Is Sample Attempt": "\u00c9s intent d'exemple", 
    "January": "Gener", 
    "July": "Juliol", 
    "June": "Juny", 
    "March": "Mar\u00e7", 
    "May": "Maig", 
    "Midnight": "Mitjanit", 
    "Must be a Staff User to Perform this request.": "Ha de ser un usuari del personal per realitzar aquesta sol\u00b7licitud.", 
    "Noon": "Migdia", 
    "Note: You are %s hour ahead of server time.": [
      "Nota: Aneu %s hora avan\u00e7ats respecte la hora del servidor.", 
      "Nota: Aneu %s hores avan\u00e7ats respecte la hora del servidor."
    ], 
    "Note: You are %s hour behind server time.": [
      "Nota: Aneu %s hora endarrerits respecte la hora del servidor.", 
      "Nota: Aneu %s hores endarrerits respecte la hora del servidor."
    ], 
    "November": "Novembre", 
    "Now": "Ara", 
    "October": "Octubre", 
    "Passed Proctoring": "Supervisat aprovat", 
    "Pending Session Review": "Revisi\u00f3 pendent de la sessi\u00f3", 
    "Practice Exam Completed": "Examen pr\u00e0ctic completat", 
    "Practice Exam Failed": "L'examen de pr\u00e0ctica ha fallat", 
    "Proctored Option Available": "Opci\u00f3 Supervisat disponible", 
    "Proctored Option No Longer Available": "L'opci\u00f3 Supervisat ja no est\u00e0 disponible", 
    "Proctoring Session Results Update for {course_name} {exam_name}": "Actualitzaci\u00f3 de resultats de la sessi\u00f3 de supervisi\u00f3 per a {course_name} {exam_name}", 
    "Ready To Start": "Llest per comen\u00e7ar", 
    "Ready To Submit": "Preparat per enviar", 
    "Rejected": "Rebutjat", 
    "Remove": "Eliminar", 
    "Remove all": "Esborrar-los tots", 
    "Retry Verification": "Reintenteu la verificaci\u00f3", 
    "Review Policy Exception": "Revisa l'excepci\u00f3 de la pol\u00edtica", 
    "Second Review Required": "Es requereix una segona revisi\u00f3", 
    "September": "Setembre", 
    "Show": "Mostrar", 
    "Start Proctored Exam": "Comen\u00e7i l'examen supervisat", 
    "Start System Check": "Comen\u00e7a la verificaci\u00f3 del sistema", 
    "Started": "Ha comen\u00e7at", 
    "Submitted": "Enviat", 
    "Take this exam without proctoring.": "Realitzeu aquest examen sense supervisi\u00f3.", 
    "Taking As Open Exam": "Prenent com a examen obert", 
    "Taking As Proctored Exam": "Realitzaci\u00f3 de l'examen supervisat", 
    "Taking as Proctored": "Tenint com supervisat", 
    "This exam has a time limit associated with it.": "Aquest examen t\u00e9 un l\u00edmit de temps associat.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Aquesta \u00e9s la llista de %s disponibles. En podeu escollir alguns seleccionant-los a la caixa de sota i fent clic a la fletxa \"Escollir\" entre les dues caixes.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Aquesta \u00e9s la llista de %s escollits. En podeu eliminar alguns seleccionant-los a la caixa de sota i fent clic a la fletxa \"Eliminar\" entre les dues caixes.", 
    "Timed Exam": "Examen temporal", 
    "Timed Out": "S'ha acabat el temps", 
    "To pass this exam, you must complete the problems in the time allowed.": "Per aprovar aquest examen, heu de completar els problemes en el temps perm\u00e8s.", 
    "Today": "Avui", 
    "Tomorrow": "Dem\u00e0", 
    "Try this practice exam again": "Torneu a provar aquest examen de pr\u00e0ctica", 
    "Type into this box to filter down the list of available %s.": "Escriviu en aquesta caixa per a filtrar la llista de %s disponibles.", 
    "Ungraded Practice Exam": "Examen de pr\u00e0ctica no graduat", 
    "Verified": "Verificat", 
    "View my exam": "Veure el meu examen", 
    "Yesterday": "Ahir", 
    "You can also retry this practice exam": "Tamb\u00e9 podeu tornar a provar aquest examen de pr\u00e0ctica", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Heu seleccionat una acci\u00f3 i no heu fet cap canvi a camps individuals. Probablement esteu cercant el bot\u00f3 'Anar' enlloc de 'Desar'.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Heu seleccionat una acci\u00f3, per\u00f2 encara no heu desat els vostres canvis a camps individuals. Si us plau premeu OK per desar. Haureu de tornar a executar l'acci\u00f3.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Teniu canvis sense desar a camps editables individuals. Si executeu una acci\u00f3, es perdran aquests canvis no desats.", 
    "active proctored exams": "ex\u00e0mens supervisats actius", 
    "could not determine the course_id": "no s'ha pogut determinar el  course_id", 
    "courses with active proctored exams": "cursos amb ex\u00e0mens supervisats actius", 
    "internally reviewed": "Revisat internament", 
    "one letter Friday\u0004F": "V", 
    "one letter Monday\u0004M": "L", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "D", 
    "one letter Thursday\u0004T": "J", 
    "one letter Tuesday\u0004T": "M", 
    "one letter Wednesday\u0004W": "X", 
    "pending": "pendent", 
    "practice": "practica", 
    "proctored": "supervisat", 
    "satisfactory": "satisfactori", 
    "timed": "cronometrat", 
    "unsatisfactory": "insatisfactori", 
    "you have less than a minute remaining": "teniu menys d'un minut romanent", 
    "you have {remaining_time} remaining": "teniu {remaining_time} romanent", 
    "you will have ": "vost\u00e8 tindr\u00e0", 
    "your course": "el vostre curs", 
    "{num_of_hours} hour": "{num_of_hours} hora", 
    "{num_of_hours} hours": "{num_of_hours} hores", 
    "{num_of_minutes} minute": "{num_of_minutes} minut", 
    "{num_of_minutes} minutes": "{num_of_minutes} minuts"
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
    "DATETIME_FORMAT": "j \\d\\e F \\d\\e Y \\a \\l\\e\\s G:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S", 
      "%d/%m/%Y %H:%M:%S.%f", 
      "%d/%m/%Y %H:%M", 
      "%d/%m/%y %H:%M:%S", 
      "%d/%m/%y %H:%M:%S.%f", 
      "%d/%m/%y %H:%M", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d"
    ], 
    "DATE_FORMAT": "j \\d\\e F \\d\\e Y", 
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y", 
      "%d/%m/%y", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j \\d\\e F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d/m/Y G:i", 
    "SHORT_DATE_FORMAT": "d/m/Y", 
    "THOUSAND_SEPARATOR": ".", 
    "TIME_FORMAT": "G:i", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M:%S.%f", 
      "%H:%M"
    ], 
    "YEAR_MONTH_FORMAT": "F \\d\\e\\l Y"
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

