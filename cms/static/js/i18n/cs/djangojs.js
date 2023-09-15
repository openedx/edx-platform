

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n == 1 && n % 1 == 0) ? 0 : (n >= 2 && n <= 4 && n % 1 == 0) ? 1: (n % 1 != 0 ) ? 2 : 3;
    if (typeof v === 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  const newcatalog = {
    "\n                After the due date has passed, you can review the exam, but you cannot change your answers.\n            ": "\nPo uplynut\u00ed term\u00ednu si m\u016f\u017eete zkou\u0161ku prohl\u00e9dnout, ale nem\u016f\u017eete sv\u00e9 odpov\u011bdi m\u011bnit.",
    "\n                The time allotted for this exam has expired. Your exam has been submitted and any work you completed\n                will be graded.\n            ": "\n\u010cas vyhrazen\u00fd pro tuto zkou\u0161ku vypr\u0161el. Va\u0161e zkou\u0161ka byla odesl\u00e1na a jak\u00e1koli pr\u00e1ce, kterou jste dokon\u010dili, bude ohodnocena.",
    "\n                You have submitted your timed exam.\n            ": "\nOdeslali jste \u010dasovanou zkou\u0161ku.",
    "\n                Your proctoring session was reviewed successfully. Go to your progress page to view your exam grade.\n            ": "\nVa\u0161e dozorovan\u00e1 relace byla \u00fasp\u011b\u0161n\u011b zkontrolov\u00e1na. P\u0159ejd\u011bte na str\u00e1nku sv\u00e9ho postupu a zobrazte hodnocen\u00ed testu.",
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\nNezav\u00edrejte toto okno p\u0159ed dokon\u010den\u00edm zkou\u0161ky. pokud toto okno zav\u0159ete, va\u0161e relace dozorov\u00e1n\u00ed skon\u010d\u00ed a dozorovanou zkou\u0161ku \u00fasp\u011b\u0161n\u011b nedokon\u010d\u00edte.",
    "\n            If you have issues relating to proctoring, you can contact %(provider_name)s technical support by emailing %(provider_tech_support_email)s  or by calling %(provider_tech_support_phone)s.\n          ": "\nPokud m\u00e1te probl\u00e9my t\u00fdkaj\u00edc\u00ed se dozorov\u00e1n\u00ed, m\u016f\u017eete kontaktovat technickou podporu %(provider_name)s e-mailem na %(provider_tech_support_email)s nebo zavol\u00e1n\u00edm na %(provider_tech_support_phone)s.",
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\nVra\u0165te se do okna kurzu %(platform_name)s a zahajte zkou\u0161ku. Kdy\u017e dokon\u010d\u00edte zkou\u0161ku a ozna\u010d\u00edte ji jako dokon\u010denou, m\u016f\u017eete toto okno zav\u0159\u00edt, \u010d\u00edm\u017e ukon\u010d\u00edte relaci dozorov\u00e1n\u00ed a nahrajete data z relace dozorov\u00e1n\u00ed ke kontrole.",
    "\n          %(platform_name)s Rules for Online Proctored Exams\n      ": "\n%(platform_name)s Pravidla pro online dozorovan\u00e9 zkou\u0161ky",
    "\n          Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n        ": "\nZkop\u00edrujte tento jedine\u010dn\u00fd k\u00f3d zkou\u0161ky. Pozd\u011bji p\u0159ed zah\u00e1jen\u00edm zkou\u0161ky budete vyzv\u00e1ni k vlo\u017een\u00ed tohoto k\u00f3du.",
    "\n          For security and exam integrity reasons, we ask you to sign in to your edX account. Then we will direct you to the RPNow proctoring experience.\n        ": "\nZ d\u016fvodu bezpe\u010dnosti a integrity testu v\u00e1s \u017e\u00e1d\u00e1me, abyste se p\u0159ihl\u00e1sili ke sv\u00e9mu \u00fa\u010dtu edX. Pot\u00e9 v\u00e1s nasm\u011brujeme na zku\u0161enost s dozorov\u00e1n\u00edm RPNow.",
    "\n          Note: As part of the proctored exam setup, you will be asked\n          to verify your identity. Before you begin, make sure you are\n          on a computer with a webcam, and that you have a valid form\n          of photo identification such as a driver\u2019s license or\n          passport.\n        ": "\nPozn\u00e1mka: V r\u00e1mci nastaven\u00ed dozorovan\u00e9 zkou\u0161ky budete po\u017e\u00e1d\u00e1ni o ov\u011b\u0159en\u00ed sv\u00e9 identity. Ne\u017e za\u010dnete, ujist\u011bte se, \u017ee pou\u017e\u00edv\u00e1te po\u010d\u00edta\u010d s webovou kamerou a \u017ee m\u00e1te platn\u00fd pr\u016fkaz toto\u017enosti s fotografi\u00ed, jako je \u0159idi\u010dsk\u00fd pr\u016fkaz nebo pas.",
    "\n          Step 1\n        ": "\nKrok 1\n       ",
    "\n          Step 2\n        ": "\nKrok 2",
    "\n          Step 3\n        ": "\nKrok 3",
    "\n          You will be guided through steps to set up online proctoring software and verify your identity.\n        ": "\nBudete provedeni kroky k nastaven\u00ed online proctoring softwaru a ov\u011b\u0159en\u00ed va\u0161\u00ed identity.",
    "\n         You must adhere to the following rules while you complete this exam.\n         <strong>If you violate these rules, you will receive a score of 0 on the exam, and you will not be eligible for academic course credit.\n         </strong></br>\n      ": "\nP\u0159i absolvov\u00e1n\u00ed t\u00e9to zkou\u0161ky mus\u00edte dodr\u017eovat n\u00e1sleduj\u00edc\u00ed pravidla. <strong>Pokud tato pravidla poru\u0161\u00edte, z\u00edsk\u00e1te ze zkou\u0161ky sk\u00f3re 0 a nebudete m\u00edt n\u00e1rok na z\u00e1po\u010det z akademick\u00e9ho kurzu.</strong></br>",
    "\n        &#8226; You have %(total_time)s to complete this exam. </br>\n        &#8226; Once you start the exam, you cannot stop the timer. </br>\n        &#8226; For all question types, you must click \"submit\" to complete your answer. </br>\n        &#8226; If time expires before you click \"End My Exam\", only your submitted answers will be graded.\n      ": "\n\u2022 K dokon\u010den\u00ed t\u00e9to zkou\u0161ky m\u00e1te %(total_time)s.</br> \n\u2022 Jakmile spust\u00edte vy\u0161et\u0159en\u00ed, nem\u016f\u017eete zastavit \u010dasova\u010d.</br> \n\u2022 U v\u0161ech typ\u016f ot\u00e1zek mus\u00edte pro dokon\u010den\u00ed odpov\u011bdi kliknout na \u201eodeslat\u201c.</br>\n\u2022 Pokud \u010das vypr\u0161\u00ed p\u0159ed kliknut\u00edm na \u201eUkon\u010dit zkou\u0161ku\u201c, budou hodnoceny pouze va\u0161e odeslan\u00e9 odpov\u011bdi.",
    "\n        A system error has occurred with your proctored exam. Please reach out to \n        <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">%(platform_name)s Support</a> for \n        assistance, and return to the exam once you receive further instructions.\n      ": "\nU va\u0161\u00ed dozorovan\u00e9 zkou\u0161ky do\u0161lo k syst\u00e9mov\u00e9 chyb\u011b. Po\u017e\u00e1dejte o pomoc <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">podporu %(platform_name)s</a> a vra\u0165te se ke zkou\u0161ce, jakmile obdr\u017e\u00edte dal\u0161\u00ed pokyny.",
    "\n        A system error has occurred with your proctored exam. Please reach out to your course \n        team at <a href=\"mailto:%(proctoring_escalation_email)s\">%(proctoring_escalation_email)s</a> \n        for assistance, and return to the exam once you receive further instructions.\n      ": "\nU va\u0161\u00ed dozorovan\u00e9 zkou\u0161ky do\u0161lo k syst\u00e9mov\u00e9 chyb\u011b. Po\u017e\u00e1dejte o pomoc sv\u016fj t\u00fdm kurzu na <a href=\"mailto:%(proctoring_escalation_email)s\">%(proctoring_escalation_email)s</a> a vra\u0165te se ke zkou\u0161ce, jakmile obdr\u017e\u00edte dal\u0161\u00ed pokyny.",
    "\n        About Proctored Exams\n        ": "\nO dozorovan\u00fdch zkou\u0161k\u00e1ch",
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\nOpravdu chcete tuto zkou\u0161ku slo\u017eit bez dozorov\u00e1n\u00ed?",
    "\n        Create your onboarding profile for faster access in the future\n      ": "\nVytvo\u0159te si sv\u016fj registra\u010dn\u00ed profil pro rychlej\u0161\u00ed p\u0159\u00edstup v budoucnu",
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\nZ d\u016fvodu nespln\u011bn\u00fdch p\u0159edpoklad\u016f m\u016f\u017eete tuto zkou\u0161ku absolvovat pouze bez dozorov\u00e1n\u00ed.",
    "\n        Establish your identity with the proctoring system to take a proctored exam\n      ": "\nZjist\u011bte svou identitu v proctoring syst\u00e9mu, abyste mohli absolvovat proctored zkou\u0161ku",
    "\n        Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n        on your grade in the course.\n      ": "\nSeznamte se s proctoringem pro skute\u010dn\u00e9 zkou\u0161ky pozd\u011bji v kurzu. Tato cvi\u010dn\u00e1 zkou\u0161ka nem\u00e1 \u017e\u00e1dn\u00fd vliv na va\u0161i zn\u00e1mku v kurzu.",
    "\n        Hello %(username)s,\n    ": "\nDobr\u00fd den %(username)s,",
    "\n        I am ready to start this timed exam.\n      ": "\nJsem p\u0159ipraven zah\u00e1jit tuto m\u011b\u0159enou zkou\u0161ku.",
    "\n        If you cannot find this email, you can <a href=\"%(reset_link)s\" target=\"_blank\">reset your password</a> to\n        activate your account.\n      ": "\nPokud tento e-mail nem\u016f\u017eete naj\u00edt, m\u016f\u017eete <a href=\"%(reset_link)s\" target=\"_blank\">si resetovat heslo</a> a aktivovat sv\u016fj \u00fa\u010det.",
    "\n        If you cannot find this email, you can reset your password to activate your account.\n      ": "\nPokud tento e-mail nem\u016f\u017eete naj\u00edt, m\u016f\u017eete si resetovat heslo a aktivovat sv\u016fj \u00fa\u010det.",
    "\n        If you have concerns about your proctoring session results, contact your course team.\n      ": "\nPokud m\u00e1te obavy ohledn\u011b v\u00fdsledk\u016f proctoring session, kontaktujte sv\u016fj t\u00fdm kurzu.",
    "\n        If you have questions about the status of your proctoring session results, contact %(platform_name)s Support.\n      ": "\nM\u00e1te-li dotazy ohledn\u011b stavu v\u00fdsledk\u016f va\u0161\u00ed relace dozorov\u00e1n\u00ed, kontaktujte podporu %(platform_name)s.",
    "\n        If you take this exam without proctoring, you will not be eligible for course credit or the MicroMasters credential if either applies to this course.\n      ": "\nPokud tuto zkou\u0161ku absolvujete bez proctoringu, nebudete m\u00edt n\u00e1rok na z\u00e1po\u010det z kurzu ani na pov\u011b\u0159en\u00ed MicroMasters, pokud se na tento kurz vztahuje kter\u00fdkoli z nich.",
    "\n        Make sure you:\n      ": "\nUjist\u011bte se:",
    "\n        No, I want to continue working.\n      ": "\nNe, chci pokra\u010dovat v pr\u00e1ci.",
    "\n        No, I'd like to continue working\n      ": "\nNe, r\u00e1d bych pokra\u010doval v pr\u00e1ci",
    "\n        Once your profile has been reviewed, you will receive an email with review results. The email will come from\n        <a href=\"mailto:%(learner_notification_from_email)s\">%(learner_notification_from_email)s</a>.\n        Make sure this email has been added to your inbox filter.\n      ": "\nJakmile bude v\u00e1\u0161 profil zkontrolov\u00e1n, obdr\u017e\u00edte e-mail s v\u00fdsledky kontroly. E-mail bude poch\u00e1zet z <a href=\"mailto:%(learner_notification_from_email)s\">%(learner_notification_from_email)s</a> . Ujist\u011bte se, \u017ee byl tento e-mail p\u0159id\u00e1n do va\u0161eho filtru doru\u010den\u00e9 po\u0161ty.",
    "\n        Please contact\n        <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a>\n        if you have questions.\n      ": "\nM\u00e1te-li dotazy, kontaktujte pros\u00edm <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> .",
    "\n        Practice exams do not affect your grade.\n        You have completed this practice exam and can continue with your course work.\n      ": "\nCvi\u010debn\u00ed zkou\u0161ky nemaj\u00ed vliv na va\u0161i zn\u00e1mku. Dokon\u010dili jste tuto cvi\u010dnou zkou\u0161ku a m\u016f\u017eete pokra\u010dovat ve sv\u00e9 pr\u00e1ci v kurzu.",
    "\n        Practice taking a proctored test\n      ": "\nProcvi\u010dte si chr\u00e1n\u011bn\u00fd test",
    "\n        Select the exam code, then copy it using Control + C (Windows) or Command + C (Mac).\n      ": "\nVyberte k\u00f3d zkou\u0161ky a pot\u00e9 jej zkop\u00edrujte pomoc\u00ed Control + C (Windows) nebo Command + C (Mac).",
    "\n        Start your system check now. A new window will open for this step and you will verify your identity.\n      ": "\nNyn\u00ed spus\u0165te kontrolu syst\u00e9mu. Pro tento krok se otev\u0159e nov\u00e9 okno a ov\u011b\u0159\u00edte svou identitu.",
    "\n        The following additional rules apply to this exam. These rules take precedence over the Rules for Online Proctored Exams.</br> </br>\n\n        %(exam_review_policy)s </br>\n      ": "\nPro tuto zkou\u0161ku plat\u00ed n\u00e1sleduj\u00edc\u00ed dodate\u010dn\u00e1 pravidla. Tato pravidla maj\u00ed p\u0159ednost p\u0159ed Pravidly pro online dozorovan\u00e9 zkou\u0161ky.</br></br> %(exam_review_policy)s</br>",
    "\n        The result will be visible after <strong id=\"wait_deadline\"> Loading... </strong>\n    ": "\nV\u00fdsledek bude viditeln\u00fd po <strong id=\"wait_deadline\">na\u010d\u00edt\u00e1n\u00ed...</strong>",
    "\n        There was a problem with your practice proctoring session\n      ": "\nVyskytl se probl\u00e9m s va\u0161\u00edm dozorovan\u00fdm cvi\u010den\u00edm",
    "\n        To appeal your proctored exam results, please reach out with any relevant information\n        about your exam at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\nChcete-li se odvolat proti v\u00fdsledk\u016fm dozorovan\u00e9 zkou\u0161ky, obra\u0165te se se v\u0161emi relevantn\u00edmi informacemi o sv\u00e9 zkou\u0161ce na <a href=\"%(contact_url)s\">%(contact_url_text)s</a> .",
    "\n        To be eligible for credit or the program credential associated with this course, you must pass the proctoring review for this exam.\n    ": "\nAbyste byli zp\u016fsobil\u00ed k z\u00edsk\u00e1n\u00ed z\u00e1po\u010dtu nebo akreditace programu spojen\u00e9ho s t\u00edmto kurzem, mus\u00edte u t\u00e9to zkou\u0161ky slo\u017eit  dozorovanou kontrolu.",
    "\n        Try a proctored exam\n      ": "\nZkuste dozorovanou zkou\u0161ku",
    "\n        You have submitted this practice proctored exam\n      ": "\nOdeslali jste tuto praktickou dozorovanou zkou\u0161ku",
    "\n        You will be guided through steps to set up online proctoring software and verify your identity.</br>\n      ": "\nBudete provedeni kroky k nastaven\u00ed online dozorovac\u00edm softwaru a ov\u011b\u0159en\u00ed va\u0161\u00ed identity.</br>",
    "\n        You will have %(total_time)s to complete your exam.\n    ": "\nK dokon\u010den\u00ed zkou\u0161ky budete m\u00edt %(total_time)s.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and the\n        course team has identified one or more violations of the proctored exam rules. Examples\n        of issues that may result in a rules violation include browsing\n        the internet, blurry or missing photo identification, using a phone,\n        or getting help from another person. As a result of the identified issue(s),\n        you did not successfully meet the proctored exam requirements.\n    ": "\nVa\u0161e dozorovan\u00e1 zkou\u0161ka \"%(exam_name)s\" v <a href=\"%(course_url)s\">%(course_name)s</a> byla zkontrolov\u00e1na a t\u00fdm kurzu zjistil jedno nebo v\u00edce poru\u0161en\u00ed dozorovan\u00fdch zku\u0161ebn\u00edch pravidel. P\u0159\u00edklady probl\u00e9m\u016f, kter\u00e9 mohou v\u00e9st k poru\u0161en\u00ed pravidel, zahrnuj\u00ed proch\u00e1zen\u00ed internetu, rozmazanou nebo chyb\u011bj\u00edc\u00ed identifikaci s fotografi\u00ed, pou\u017e\u00edv\u00e1n\u00ed telefonu nebo z\u00edsk\u00e1n\u00ed pomoci od jin\u00e9 osoby. V d\u016fsledku zji\u0161t\u011bn\u00fdch probl\u00e9m\u016f jste nesplnili po\u017eadavky dozorovan\u00e9 zkou\u0161ky.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and you\n        met all proctoring requirements.\n    ": "\nVa\u0161e dozorovan\u00e1 zkou\u0161ka \"%(exam_name)s\" v <a href=\"%(course_url)s\">%(course_name)s</a> byla zkontrolov\u00e1na a splnili jste v\u0161echny po\u017eadavky na dozorov\u00e1n\u00ed.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was submitted\n        successfully and will now be reviewed to ensure all exam\n        rules were followed. You should receive an email with your exam\n        status within 5 business days.\n    ": "\nVa\u0161e dozorovan\u00e1 zkou\u0161ka \"%(exam_name)s\" v <a href=\"%(course_url)s\">%(course_name)s</a> byla \u00fasp\u011b\u0161n\u011b odesl\u00e1na a nyn\u00ed bude zkontrolov\u00e1na, aby bylo zaji\u0161t\u011bno dodr\u017een\u00ed v\u0161ech pravidel zkou\u0161ky. Do 5 pracovn\u00edch dn\u016f byste m\u011bli obdr\u017eet e-mail se stavem zkou\u0161ky.",
    "\n        Your proctoring session ended before you completed this practice exam.\n        You can retry this practice exam if you had problems setting up the online proctoring software.\n      ": "\nVa\u0161e proctoring relace skon\u010dila p\u0159ed dokon\u010den\u00edm t\u00e9to praktick\u00e9 zkou\u0161ky. \nPokud jste m\u011bli probl\u00e9my s nastaven\u00edm online proctoring softwaru, m\u016f\u017eete tuto cvi\u010dnou zkou\u0161ku zkusit znovu.",
    "\n        Your proctoring session was reviewed, but did not pass all requirements\n      ": "\nVa\u0161e proctoring session byla zkontrolov\u00e1na, ale nesplnila v\u0161echny po\u017eadavky",
    "\n      Additional Exam Rules\n    ": "\nDodate\u010dn\u00e1 pravidla Zkou\u0161ky",
    "\n      After you submit your exam, your exam will be graded.\n    ": "\nPo odesl\u00e1n\u00ed zkou\u0161ky bude va\u0161e zkou\u0161ka ohodnocena.",
    "\n      Alternatively, you can end your exam.\n    ": "\nP\u0159\u00edpadn\u011b m\u016f\u017eete zkou\u0161ku ukon\u010dit.",
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\nJste si jisti, \u017ee chcete odeslat test na \u010das?",
    "\n      Are you sure you want to end your proctored exam?\n    ": "\nOpravdu chcete ukon\u010dit dozorovanou zkou\u0161ku?",
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\nVzhledem k tomu, \u017ee term\u00edn vypr\u0161el, nem\u016f\u017eete ji\u017e tuto zkou\u0161ku absolvovat.",
    "\n      Error with proctored exam\n    ": "\nChyba u dozorovan\u00e9 zkou\u0161ky",
    "\n      If you already have an onboarding profile approved through another course,\n      this submission will not be reviewed. You may retry this exam at any time\n      to validate that your setup still meets the requirements for proctoring.\n    ": "\nPokud ji\u017e m\u00e1te registra\u010dn\u00ed profil schv\u00e1len\u00fd prost\u0159ednictv\u00edm jin\u00e9ho kurzu, \ntento p\u0159\u00edsp\u011bvek nebude zkontrolov\u00e1n. Tuto zkou\u0161ku m\u016f\u017eete kdykoli zopakovat, \nabyste ov\u011b\u0159ili, \u017ee va\u0161e nastaven\u00ed st\u00e1le spl\u0148uje po\u017eadavky na proctoring.",
    "\n      If you continue to have trouble please contact <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">\n      %(platform_name)s Support</a>.\n    ": "\nPokud pot\u00ed\u017ee p\u0159etrv\u00e1vaj\u00ed, kontaktujte <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">podporu %(platform_name)s</a> .",
    "\n      If you do not have an onboarding profile with the system,\n      Verificient will review your submission and create an onboarding\n      profile to grant you access to proctored exams. Onboarding\n      profile review can take 2+ business days.\n    ": "\nPokud nem\u00e1te registra\u010dn\u00ed profil v syst\u00e9mu, \nVerificient zkontroluje v\u00e1\u0161 p\u0159\u00edsp\u011bvek a vytvo\u0159\u00ed registra\u010dn\u00ed profil, \nkter\u00fd v\u00e1m umo\u017en\u00ed p\u0159\u00edstup k chr\u00e1n\u011bn\u00fdm zkou\u0161k\u00e1m. Kontrola profilu \nregistrace m\u016f\u017ee trvat v\u00edce ne\u017e 2 pracovn\u00ed dny.",
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\nPokud m\u00e1te zdravotn\u00ed posti\u017een\u00ed,\nm\u016f\u017eete m\u00edt n\u00e1rok na dodate\u010dn\u00fd \u010dasov\u00fd p\u0159\u00edsp\u011bvek na \u010dasov\u011b omezen\u00e9 zkou\u0161ky.\nInformace o dodate\u010dn\u00fdch \u010dasov\u00fdch \u00falev\u00e1ch z\u00edsk\u00e1te od t\u00fdmu va\u0161eho kurzu.",
    "\n      If you have made an error in this submission you may restart the onboarding process. \n      Your current submission will be removed and will not receive a review.\n    ": "\nPokud jste v tomto odesl\u00e1n\u00ed ud\u011blali chybu, m\u016f\u017eete proces registrace znovu spustit. V\u00e1\u0161 aktu\u00e1ln\u00ed p\u0159\u00edsp\u011bvek bude odstran\u011bn a nebude zkontrolov\u00e1n.",
    "\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\nM\u00e1te-li dotazy ohledn\u011b stavu v\u00fdsledk\u016f dozorovan\u00fdch zkou\u0161ek, kontaktujte podporu %(platform_name)s.",
    "\n      If you have questions about the status of your requirements, contact %(platform_name)s Support.\n    ": "\nM\u00e1te-li dotazy ohledn\u011b stavu va\u0161ich po\u017eadavk\u016f, kontaktujte podporu %(platform_name)s.",
    "\n      Important\n    ": "\n          D\u016fle\u017eit\u00e9\n   ",
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\nP\u0159ed odesl\u00e1n\u00edm zkou\u0161ky se ujist\u011bte, \u017ee jste u ka\u017ed\u00e9ho probl\u00e9mu zvolili mo\u017enost \"Odeslat\".",
    "\n      Once your profile has been reviewed, you will receive an email\n      with review results. The email will come from\n      <a href=\"mailto:%(learner_notification_from_email)s\">\n        %(learner_notification_from_email)s\n      </a>,\n      so make sure this email has been added to your inbox filter.\n    ": "\nJakmile bude v\u00e1\u0161 profil zkontrolov\u00e1n, obdr\u017e\u00edte e-mail s v\u00fdsledky kontroly. E-mail bude poch\u00e1zet z <a href=\"mailto:%(learner_notification_from_email)s\">%(learner_notification_from_email)s</a> , tak\u017ee se ujist\u011bte, \u017ee byl tento e-mail p\u0159id\u00e1n do va\u0161eho filtru doru\u010den\u00e9 po\u0161ty.",
    "\n      Please check your registered email's Inbox and Spam folders for an activation email from\n      %(platform_name)s.\n    ": "\nZkontrolujte pros\u00edm ve slo\u017ece Doru\u010den\u00e1 po\u0161ta a Spam sv\u00e9ho registrovan\u00e9ho e-mailu aktiva\u010dn\u00ed e-mail od %(platform_name)s.",
    "\n      Please complete an onboarding exam before attempting this exam.\n    ": "\nP\u0159ed pokusem o tuto zkou\u0161ku dokon\u010dete vstupn\u00ed zkou\u0161ku.",
    "\n      Please contact\n      <a href=\"mailto:%(integration_specific_email)s\">\n        %(integration_specific_email)s\n      </a> if you have questions.\n    ": "\nM\u00e1te-li dotazy, kontaktujte pros\u00edm <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> .",
    "\n      Please contact\n      <a href=\"mailto:%(integration_specific_email)s\">\n        %(integration_specific_email)s\n      </a> if you have questions. You may retake this onboarding exam by clicking \"Retry my exam\".\n    ": "\nM\u00e1te-li dotazy, kontaktujte pros\u00edm <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> . Tuto vstupn\u00ed zkou\u0161ku m\u016f\u017eete znovu absolvovat kliknut\u00edm na \u201eOpakovat zkou\u0161ku\u201c.",
    "\n      Proctored Exam Rules\n    ": "\nPravidla dozorovan\u00e9 zkou\u0161ky",
    "\n      Proctoring for this course is provided via %(provider_name)s.  Onboarding review, including identity verification, can take 2+ business days.\n    ": "\nDozorov\u00e1n\u00ed pro tento kurz je poskytov\u00e1n prost\u0159ednictv\u00edm %(provider_name)s. Kontrola registrace, v\u010detn\u011b ov\u011b\u0159en\u00ed identity, m\u016f\u017ee trvat d\u00e9le ne\u017e 2 pracovn\u00ed dny.",
    "\n      Proctoring for your exam is provided via %(provider_name)s.\n      If you have questions about the status of your onboarding exam, contact\n      <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a>.\n    ": "\nDozor pro va\u0161i zkou\u0161ku je poskytov\u00e1n prost\u0159ednictv\u00edm %(provider_name)s. Pokud m\u00e1te dotazy ohledn\u011b stavu va\u0161\u00ed vstupn\u00ed zkou\u0161ky, kontaktujte <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> .",
    "\n      Set up and start your proctored exam\n    ": "\nNastavte a spus\u0165te dozorovanou zkou\u0161ku",
    "\n      The content of this exam can only be viewed through the RPNow\n      application. If you have yet to complete your exam, please\n      return to the RPNow application to proceed.\n    ": "\nObsah t\u00e9to zkou\u0161ky lze zobrazit pouze prost\u0159ednictv\u00edm aplikace RPNow. Pokud je\u0161t\u011b nem\u00e1te zkou\u0161ku dokon\u010denou, vra\u0165te se do aplikace RPNow a pokra\u010dujte.",
    "\n      The due date for this exam has passed\n    ": "\nTerm\u00edn pro tuto zkou\u0161ku ji\u017e uplynul",
    "\n      This exam is proctored\n    ": "\nTato zkou\u0161ka je dozorovan\u00e1",
    "\n      To be eligible for credit or the program credential associated with this course, you must pass the proctoring review for this exam.\n\n    ": "\nAbyste byli zp\u016fsobil\u00ed k z\u00edsk\u00e1n\u00ed z\u00e1po\u010dtu nebo akreditace programu spojen\u00e9ho s t\u00edmto kurzem, mus\u00edte u t\u00e9to zkou\u0161ky slo\u017eit ov\u011b\u0159en\u00ed dozorov\u00e1n\u00ed.",
    "\n      To view your exam questions and responses, select <strong>View my exam</strong>. The exam's review status is shown in the left navigation pane.\n    ": "\nChcete-li zobrazit ot\u00e1zky a odpov\u011bdi ke zkou\u0161ce, vyberte <strong>Zobrazit moji zkou\u0161ku</strong> . Stav kontroly vy\u0161et\u0159en\u00ed se zobrazuje v lev\u00e9m naviga\u010dn\u00edm panelu.",
    "\n      Why this is important to you:\n    ": "\nPro\u010d je to pro v\u00e1s d\u016fle\u017eit\u00e9:",
    "\n      Yes, submit my timed exam.\n    ": "\nAno, odeslat moji \u010dasovou zkou\u0161ku.",
    "\n      You are taking \"%(exam_display_name)s\" as an onboarding exam. You must click \u201cYes, end my proctored exam\u201d and submit your proctoring session to complete onboarding.\n    ": "\nAbsolvujete \u201e%(exam_display_name)s\u201c jako vstupn\u00ed zkou\u0161ku. Pro dokon\u010den\u00ed registrace mus\u00edte kliknout na \u201eAno, ukon\u010dit mou dozorovanou zkou\u0161ku\u201c a odeslat svou dozorovanou relaci.",
    "\n      You have not activated your account.\n    ": "\nNeaktivovali jste sv\u016fj \u00fa\u010det.",
    "\n      You have submitted this proctored exam for review\n    ": "\nOdeslali jste tuto dozorovanou zkou\u0161ku ke kontrole",
    "\n      You must complete an onboarding exam before taking this proctored exam\n    ": "\nP\u0159ed slo\u017een\u00edm t\u00e9to chr\u00e1n\u011bn\u00e9 zkou\u0161ky mus\u00edte absolvovat vstupn\u00ed zkou\u0161ku",
    "\n      Your %(platform_name)s account has not yet been activated. To take the proctored exam,\n      you are required to activate your account.\n    ": "\nV\u00e1\u0161 \u00fa\u010det %(platform_name)s je\u0161t\u011b nebyl aktivov\u00e1n. Abyste mohli absolvovat dozorovanou zkou\u0161ku, mus\u00edte si aktivovat sv\u016fj \u00fa\u010det.",
    "\n      Your exam is ready to be resumed.\n    ": "\nVa\u0161e zkou\u0161ka je p\u0159ipravena k obnoven\u00ed.",
    "\n      Your onboarding exam failed to pass all requirements.\n    ": "\nVa\u0161e vstupn\u00ed zkou\u0161ka nesplnila v\u0161echny po\u017eadavky.",
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\nV\u00fdsledky dozoru va\u0161eho cvi\u010den\u00ed: <b class=\"failure\">Neuspokojiv\u00e9</b>",
    "\n      Your profile has been established, and you're ready to take proctored exams in this course.\n    ": "\nV\u00e1\u0161 profil byl zalo\u017een a jste p\u0159ipraveni skl\u00e1dat proctored zkou\u0161ky v tomto kurzu.",
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n%(exam_name)s je m\u011b\u0159en\u00e1 zkou\u0161ka (%(total_time)s)",
    "\n    Error: There was a problem with your onboarding session\n  ": "\nChyba: Vyskytl se probl\u00e9m s va\u0161\u00ed registra\u010dn\u00ed relac\u00ed",
    "\n    If you have any questions about your results, you can reach out at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\nPokud m\u00e1te n\u011bjak\u00e9 dotazy ohledn\u011b sv\u00fdch v\u00fdsledk\u016f, m\u016f\u017eete se obr\u00e1tit na <a href=\"%(contact_url)s\">%(contact_url_text)s</a> .",
    "\n    Proctoring onboarding exam\n  ": "\nDozorovan\u00e1 vstupn\u00ed zkou\u0161ka",
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\nN\u00e1sleduj\u00edc\u00ed p\u0159edb\u011b\u017en\u00e9 podm\u00ednky jsou ve stavu <strong>\u010dek\u00e1n\u00ed</strong> a mus\u00ed b\u00fdt \u00fasp\u011b\u0161n\u011b dokon\u010deny, abyste mohli pokra\u010dovat:",
    "\n    You can take this exam with proctoring only when all prerequisites have been successfully completed.\n    ": "\nTuto zkou\u0161ku s dozorov\u00e1n\u00edm m\u016f\u017eete absolvovat a\u017e po \u00fasp\u011b\u0161n\u00e9m spln\u011bn\u00ed v\u0161ech p\u0159edpoklad\u016f.",
    "\n    You did not satisfy the following prerequisites:\n    ": "\nNesplnili jste n\u00e1sleduj\u00edc\u00ed p\u0159edpoklady:",
    "\n    You did not satisfy the requirements for taking this exam with proctoring.\n    ": "\nNesplnili jste po\u017eadavky pro slo\u017een\u00ed t\u00e9to zkou\u0161ky s proktoringem.",
    "\n    You have not completed the prerequisites for this exam. All requirements must be satisfied before you can take this proctored exam.\n    ": "\nNesplnili jste p\u0159edpoklady pro tuto zkou\u0161ku. P\u0159ed slo\u017een\u00edm t\u00e9to chr\u00e1n\u011bn\u00e9 zkou\u0161ky mus\u00ed b\u00fdt spln\u011bny v\u0161echny po\u017eadavky.\n    ",
    "\n    You have submitted this onboarding exam\n  ": "\nOdeslali jste tuto vstupn\u00ed zkou\u0161ku",
    "\n    You will be guided through online proctoring software set up and identity verification.\n  ": "\nProvedeme v\u00e1s nastaven\u00edm online dozorovac\u00edm softwarem a ov\u011b\u0159en\u00edm identity.",
    "\n    Your onboarding exam is being reviewed. Before attempting this exam, please allow 2+ business days for your onboarding exam to be reviewed.\n  ": "\nVa\u0161e vstupn\u00ed zkou\u0161ka se kontroluje. Ne\u017e se pokus\u00edte o tento test, po\u010dkejte pros\u00edm 2 nebo v\u00edce pracovn\u00edch dn\u016f, ne\u017e bude va\u0161e vstupn\u00ed zkou\u0161ka zkontrolov\u00e1na.",
    "\n    Your onboarding profile was reviewed successfully\n  ": "\nV\u00e1\u0161 registra\u010dn\u00ed profil byl \u00fasp\u011b\u0161n\u011b zkontrolov\u00e1n",
    "\n    Your onboarding session was reviewed, but did not pass all requirements\n  ": "\nVa\u0161e vstupn\u00ed relace byla zkontrolov\u00e1na, ale nesplnila v\u0161echny po\u017eadavky",
    "\n    Your proctoring session ended before you completed this onboarding exam.\n    You should retry this onboarding exam.\n  ": "\nVa\u0161e proctoring relace skon\u010dila p\u0159ed dokon\u010den\u00edm t\u00e9to vstupn\u00ed zkou\u0161ky. Tuto vstupn\u00ed zkou\u0161ku byste m\u011bli zkusit znovu.",
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": "Od tohoto okam\u017eiku mus\u00edte dodr\u017eovat <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">pravidla online dozorov\u00e1n\u00ed,</a> abyste u sv\u00e9 zkou\u0161ky pro\u0161li kontrolou dozoru.",
    " Your Proctoring Session Has Started ": "Va\u0161e dozorovan\u00e1 relace za\u010dala",
    " and {num_of_minutes} minute": "a {num_of_minutes} minut",
    " and {num_of_minutes} minutes": "a {num_of_minutes} minut",
    " to complete and submit the exam.": "dokon\u010dit a odevzdat zkou\u0161ku.",
    "%(sel)s of %(cnt)s selected": [
      "Vybr\u00e1na je %(sel)s polo\u017eka z celkem %(cnt)s.",
      "Vybr\u00e1ny jsou %(sel)s polo\u017eky z celkem %(cnt)s.",
      "Vybran\u00fdch je %(sel)s polo\u017eek z celkem %(cnt)s.",
      "Vybran\u00fdch je %(sel)s polo\u017eek z celkem %(cnt)s."
    ],
    "(required):": "(vy\u017eadovan\u00e9):",
    "6 a.m.": "6h r\u00e1no",
    "6 p.m.": "6h ve\u010der",
    "Additional Time (minutes)": "Dal\u0161\u00ed \u010das (v minut\u00e1ch)",
    "After you select ": "Pot\u00e9, co vyberete",
    "All Unreviewed": "V\u0161e nezkontrolov\u00e1no",
    "All Unreviewed Failures": "V\u0161echna nezkontrolovan\u00e1 selh\u00e1n\u00ed",
    "April": "duben",
    "Are you sure you want to delete the following file? It cannot be restored.\nFile: ": "Jste si opravdu jisti, \u017ee chcete odstranit n\u00e1sleduj\u00edc\u00ed soubor? Soubor nem\u016f\u017ee b\u00fdt obnoven.\nSoubor: ",
    "Assessment": "Hodnocen\u00ed",
    "Assessments": "Hodnocen\u00ed",
    "August": "srpen",
    "Available %s": "Dostupn\u00e9 polo\u017eky: %s",
    "Back to Full List": "Zp\u011bt na cel\u00fd seznam",
    "Block view is unavailable": "Zobrazen\u00ed blok\u016f nen\u00ed k dispozici",
    "Can I request additional time to complete my exam?": "Mohu po\u017e\u00e1dat o dal\u0161\u00ed \u010das na dokon\u010den\u00ed zkou\u0161ky?",
    "Cancel": "Storno",
    "Cannot update attempt review status": "Stav kontroly pokusu nelze aktualizovat",
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Zm\u011bny krok\u016f, kter\u00e9 nejsou vybr\u00e1ny jako sou\u010d\u00e1st p\u0159i\u0159azen\u00ed, nebudou ulo\u017eeny.",
    "Choose": "Vybrat",
    "Choose a Date": "Vyberte datum",
    "Choose a Time": "Vyberte \u010das",
    "Choose a time": "Vyberte \u010das",
    "Choose all": "Vybrat v\u0161e",
    "Chosen %s": "Vybran\u00e9 polo\u017eky %s",
    "Click to choose all %s at once.": "Chcete-li najednou vybrat v\u0161echny polo\u017eky %s, klepn\u011bte sem.",
    "Click to remove all chosen %s at once.": "Chcete-li najednou odebrat v\u0161echny vybran\u00e9 polo\u017eky %s, klepn\u011bte sem.",
    "Close": "Zav\u0159\u00edt",
    "Confirm": "Potvrdit",
    "Confirm Delete Uploaded File": "Potvr\u010fte smaz\u00e1n\u00ed nahran\u00e9ho souboru",
    "Confirm Grade Team Submission": "Potvr\u010fte odevzd\u00e1n\u00ed t\u00fdmov\u00e9ho hodnocen\u00ed",
    "Confirm Submit Response": "Potvr\u010fte odesl\u00e1n\u00ed odpov\u011bdi",
    "Continue Exam Without Proctoring": "Pokra\u010dovat ve zkou\u0161ce bez dozoru",
    "Continue to my practice exam": "Pokra\u010dujte k m\u00e9 praktick\u00e9 zkou\u0161ce",
    "Continue to my proctored exam.": "Pokra\u010dujte k m\u00e9 dozorovan\u00e9 zkou\u0161ce.",
    "Continue to onboarding": "Pokra\u010dujte k registraci",
    "Copy Exam Code": "Zkop\u00edrujte k\u00f3d zkou\u0161ky",
    "Could not load teams information.": "Nepoda\u0159ilo se na\u010d\u00edst informace o t\u00fdmech.",
    "Could not retrieve download url.": "Nelze z\u00edskat url pro stahov\u00e1n\u00ed.",
    "Could not retrieve upload url.": "Nelze z\u00edskat url pro nahr\u00e1v\u00e1n\u00ed.",
    "Course Id": "ID kurzu",
    "Created": "Vytvo\u0159eno",
    "Criterion Added": "Krit\u00e9rium p\u0159id\u00e1no",
    "Criterion Deleted": "Krit\u00e9rium smaz\u00e1no",
    "December": "prosinec",
    "Declined": "Odm\u00edtnuto",
    "Demo the new Grading Experience": "P\u0159edve\u010fte nov\u00e9 hodnocen\u00ed",
    "Describe ": "Popsat",
    "Download Software Clicked": "Sta\u017een\u00ed softwaru Kliknuto",
    "End My Exam": "Ukon\u010dit mou zkou\u0161ku",
    "Ending Exam": "Z\u00e1v\u011bre\u010dn\u00e1 zkou\u0161ka",
    "Enter a valid positive value number": "Zadejte platn\u00e9 kladn\u00e9 \u010d\u00edslo",
    "Enter a valid username or email": "Zadejte platn\u00e9 u\u017eivatelsk\u00e9 jm\u00e9no nebo e-mail",
    "Error": "Chyba",
    "Error getting the number of ungraded responses": "Vyskytla se chyba pri z\u00edsk\u00e1v\u00e1n\u00ed po\u010dtu neklasifikovan\u00fdch odpov\u011bd\u00ed",
    "Error when looking up username": "Hled\u00e1n\u00ed u\u017eivatelsk\u00e9ho jm\u00e9na selhalo",
    "Error while fetching student data.": "Vyskytla se chyba p\u0159i z\u00edsk\u00e1v\u00e1n\u00ed dat studenta",
    "Errors detected on the following tabs: ": "Chyby zji\u0161t\u011bn\u00e9 na n\u00e1sleduj\u00edc\u00edch kart\u00e1ch:",
    "Failed Proctoring": "Dozorov\u00e1n\u00ed se nezda\u0159ilo",
    "Failed to clone rubric": "Klonov\u00e1n\u00ed rubriky se nezda\u0159ilo",
    "February": "\u00fanor",
    "Feedback available for selection.": "Zp\u011btn\u00e1 vazba k dispozici pro v\u00fdb\u011br.",
    "File types can not be empty.": "Typ souboru nem\u016f\u017ee b\u00fdt pr\u00e1zdn\u00fd",
    "File upload failed: unsupported file type. Only the supported file types can be uploaded. If you have questions, please reach out to the course team.": "Nahr\u00e1n\u00ed souboru se nezda\u0159ilo: nepodporovan\u00fd typ souboru. Nahr\u00e1t lze pouze podporovan\u00e9 typy soubor\u016f. M\u00e1te-li dotazy, obra\u0165te se na t\u00fdm kurzu.",
    "Filter": "Filtr",
    "Final Grade Received": "P\u0159ijato z\u00e1v\u011bre\u010dn\u00e9 hodnocen\u00ed",
    "Go Back": "J\u00edt zp\u011bt",
    "Grade Status": "Stav klasifikace",
    "Have a computer with a functioning webcam": "M\u00edt po\u010d\u00edta\u010d s funk\u010dn\u00ed webovou kamerou",
    "Have your valid photo ID (e.g. driver's license or passport) ready": "P\u0159ipravte si platn\u00fd pr\u016fkaz toto\u017enosti s fotografi\u00ed (nap\u0159. \u0159idi\u010dsk\u00fd pr\u016fkaz nebo pas).",
    "Heading 3": "Nadpis 3",
    "Heading 4": "Nadpis 4",
    "Heading 5": "Nadpis 5",
    "Heading 6": "Nadpis 6",
    "Hide": "Skr\u00fdt",
    "However, {overwritten_count} of these students have received a grade through the staff grade override tool already.": "{overwritten_count} z t\u011bchto student\u016f v\u0161ak ji\u017e obdr\u017eeli zn\u00e1mku prost\u0159ednictv\u00edm n\u00e1stroje pro p\u0159epis hodnocen\u00ed u\u010ditel\u016f.",
    "I am ready to start this timed exam,": "Jsem p\u0159ipraven zah\u00e1jit tuto m\u011b\u0159enou zkou\u0161ku,",
    "I understand and want to reset this onboarding exam.": "Rozum\u00edm a chci resetovat tuto vstupn\u00ed zkou\u0161ku.",
    "If the proctoring software window is still open, close it now and confirm that you want to quit the application.": "Pokud je okno proctoring software st\u00e1le otev\u0159en\u00e9, zav\u0159ete jej nyn\u00ed a potvr\u010fte, \u017ee chcete ukon\u010dit aplikaci.",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Pokud opust\u00edte tuto str\u00e1nku bez ulo\u017een\u00ed nebo odesl\u00e1n\u00ed odpov\u011bdi, ztrat\u00edte v\u0161echnu pr\u00e1ci, kterou jste na odpov\u011bdi vykonali.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Pokud opust\u00edte tuto str\u00e1nku bez odesl\u00e1n\u00ed sv\u00e9ho vz\u00e1jemn\u00e9ho hodnocen\u00ed, ztrat\u00edte v\u0161echnu pr\u00e1ci.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Pokud opust\u00edte tuto str\u00e1nku bez odesl\u00e1n\u00ed sv\u00e9ho sebehodnocen\u00ed, ztrat\u00edte v\u0161echnu pr\u00e1ci.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Pokud opust\u00edte tuto str\u00e1nku bez odesl\u00e1n\u00ed sv\u00e9ho hodnocen\u00ed u\u010ditel\u016f, ztrat\u00edte v\u0161echnu pr\u00e1ci.",
    "Individual file size must be {max_files_mb}MB or less.": "Jednotliv\u00e9 soubory mus\u00ed m\u00edt velikost {max_files_mb}MB nebo m\u00e9n\u011b.",
    "Is Resumable": "Je mo\u017en\u00e9 obnovit",
    "Is Sample Attempt": "Je uk\u00e1zkov\u00fd pokus",
    "January": "leden",
    "July": "\u010dervenec",
    "June": "\u010derven",
    "List of Open Assessments is unavailable": "Seznam otev\u0159en\u00fdch hodnocen\u00ed nen\u00ed k dispozici",
    "Make sure that you have selected \"Submit\" for each answer before you submit your exam.": "P\u0159ed odesl\u00e1n\u00edm zkou\u0161ky se ujist\u011bte, \u017ee jste u ka\u017ed\u00e9 odpov\u011bdi vybrali \u201eOdeslat\u201c.",
    "March": "b\u0159ezen",
    "May": "kv\u011bten",
    "Midnight": "P\u016flnoc",
    "Missing required query parameter course_id": "Chyb\u00ed po\u017eadovan\u00fd parametr dotazu course_id",
    "Multiple teams returned for course": "N\u011bkolik t\u00fdm\u016f se vr\u00e1tilo do kurzu",
    "Must be a Staff User to Perform this request.": "K proveden\u00ed tohoto po\u017eadavku mus\u00edte b\u00fdt u\u010ditelem.",
    "Navigate to onboarding exam": "P\u0159ejd\u011bte na vstupn\u00ed zkou\u0161ku",
    "No exams in course {course_id}.": "\u017d\u00e1dn\u00e9 zkou\u0161ky v kurzu {course_id}.",
    "No instructor dashboard for {proctor_service}": "\u017d\u00e1dn\u00fd panel instruktora pro {proctor_service}",
    "No onboarding status API for {proctor_service}": "\u017d\u00e1dn\u00e9 rozhran\u00ed API pro stav registrace pro {proctor_service}",
    "No proctored exams in course {course_id}": "\u017d\u00e1dn\u00e9 chr\u00e1n\u011bn\u00e9 zkou\u0161ky v kurzu {course_id}",
    "Noon": "Poledne",
    "Not Selected": "Nevybran\u00fd",
    "Note: You are %s hour ahead of server time.": [
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das o %s hodinu p\u0159edstihuje \u010das na serveru.",
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das o %s hodiny p\u0159edstihuje \u010das na serveru.",
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das o %s hodiny p\u0159edstihuje \u010das na serveru.",
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das o %s hodin p\u0159edstihuje \u010das na serveru."
    ],
    "Note: You are %s hour behind server time.": [
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das se o %s hodinu zpo\u017e\u010fuje za \u010dasem na serveru.",
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das se o %s hodiny zpo\u017e\u010fuje za \u010dasem na serveru.",
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das se o %s hodiny zpo\u017e\u010fuje za \u010dasem na serveru.",
      "Pozn\u00e1mka: V\u00e1\u0161 \u010das se o %s hodin zpo\u017e\u010fuje za \u010dasem na serveru."
    ],
    "November": "listopad",
    "Now": "Nyn\u00ed",
    "October": "\u0159\u00edjen",
    "Onboarding Expired": "Platnost registrace vypr\u0161ela",
    "Onboarding Failed": "Registrace se nezda\u0159ila",
    "Onboarding Missing": "Chyb\u00ed registrace",
    "Onboarding Pending": "Registrace \u010dek\u00e1 na vy\u0159\u00edzen\u00ed",
    "Onboarding status question": "Ot\u00e1zka stavu registrace",
    "Once you click \"Yes, end my proctored exam\", the exam will be closed, and your proctoring session will be submitted for review.": "Jakmile kliknete na \u201eAno, ukon\u010dit mou dozorovanou zkou\u0161ku\u201c, bude zkou\u0161ka uzav\u0159ena a va\u0161e dozorovan\u00e1 relace bude odesl\u00e1na ke kontrole.",
    "One or more rescheduling tasks failed.": "Jedna nebo v\u00edce zm\u011bn term\u00edn\u016f selhaly.",
    "Option Deleted": "Mo\u017enost odebr\u00e1na",
    "Paragraph": "Odstavec",
    "Passed Proctoring": "Dozor prob\u011bhl",
    "Peer": "Spolu\u017e\u00e1ci",
    "Peer Responses Received": "P\u0159ijat\u00e9 odpov\u011bdi spolu\u017e\u00e1k\u016f",
    "Peers Assessed": "Hodnoceno spolu\u017e\u00e1ky",
    "Pending Session Review": "\u010cek\u00e1 na kontrolu relace",
    "Please wait": "\u010cekejte pros\u00edm",
    "Practice Exam Completed": "Cvi\u010dn\u00e1 zkou\u0161ka dokon\u010dena",
    "Practice Exam Failed": "Cvi\u010dn\u00e1 zkou\u0161ka se nezda\u0159ila",
    "Preformatted": "P\u0159edem naform\u00e1tov\u00e1no",
    "Problem cloning rubric": "Rubrika Probl\u00e9m klonov\u00e1n\u00ed",
    "Proctored Option Available": "Mo\u017enost dozorov\u00e1n\u00ed k dispozici",
    "Proctored Option No Longer Available": "Mo\u017enost dozorov\u00e1n\u00ed ji\u017e nen\u00ed k dispozici",
    "Proctored exam {exam_name} in {course_name} for user {username}": "Dozorovan\u00e1 zkou\u0161ka {exam_name} v {course_name} pro u\u017eivatele {username}",
    "Proctoring Results For {course_name} {exam_name}": "V\u00fdsledky dozoru pro {course_name} {exam_name}",
    "Proctoring Review In Progress For {course_name} {exam_name}": "Prob\u00edh\u00e1 kontrola Proctoring pro {course_name} {exam_name}",
    "Proctoring results are usually available within 5 business days after you submit your exam.": "V\u00fdsledky dozorov\u00e1n\u00ed jsou obvykle k dispozici do 5 pracovn\u00edch dn\u016f po odesl\u00e1n\u00ed testu.",
    "Ready To Start": "P\u0159ipraven za\u010d\u00edt",
    "Ready To Submit": "P\u0159ipraveno k odesl\u00e1n\u00ed",
    "Ready to Resume": "P\u0159ipraveno k obnoven\u00ed",
    "Refresh": "Obnovit",
    "Rejected": "Odm\u00edtnuto",
    "Remove": "Odebrat",
    "Remove all": "Odebrat v\u0161e",
    "Resetting Onboarding Exam": "Resetov\u00e1n\u00ed vstupn\u00ed zkou\u0161ky",
    "Resumed": "Obnoveno",
    "Retry my exam": "Opakujte zkou\u0161ku",
    "Review Policy Exception": "V\u00fdjimka z\u00e1sad revize",
    "Save Unsuccessful": "Ukl\u00e1d\u00e1n\u00ed se nezda\u0159ilo",
    "Second Review Required": "Druh\u00e9 p\u0159ezkoum\u00e1n\u00ed je vy\u017eadov\u00e1no",
    "Self": "Vlastn\u00ed",
    "September": "z\u00e1\u0159\u00ed",
    "Server error.": "Chyba serveru.",
    "Show": "Zobrazit",
    "Staff": "U\u010ditel\u00e9",
    "Staff Grader": "U\u010ditelsk\u00fd srovn\u00e1va\u010d",
    "Staff assessment": "Hodnocen\u00ed u\u010ditel\u016f",
    "Start Exam": "Zah\u00e1jit zkou\u0161ku",
    "Start System Check": "Spus\u0165te kontrolu syst\u00e9mu",
    "Start my exam": "Za\u010d\u00edt moji zkou\u0161ku",
    "Started": "Zah\u00e1jeno",
    "Starting Exam": "Po\u010d\u00e1te\u010dn\u00ed zkou\u0161ka",
    "Submitted": "Odevzd\u00e1no",
    "Take this exam without proctoring.": "Absolvujte tuto zkou\u0161ku bez dozoru.",
    "Taking As Open Exam": "Skl\u00e1d\u00e1n\u00ed jako otev\u0159en\u00e1 zkou\u0161ka",
    "Taking As Proctored Exam": "Absolvov\u00e1n\u00ed zkou\u0161ky jako Dozorovan\u00e9",
    "Taking as Proctored": "Podstoupit jako dozorovanou",
    "The \"{name}\" problem is configured to require a minimum of {min_grades} peer grades, and asks to review {min_graded} peers.": "Probl\u00e9m \u201e{name}\u201c je nakonfigurov\u00e1n tak, aby vy\u017eadoval minim\u00e1ln\u011b {min_grades} rovnocenn\u00e9 hodnocen\u00ed a po\u017eadoval kontrolu {min_graded} spolu\u017e\u00e1k\u016f.",
    "The display of ungraded and checked out responses could not be loaded.": "Zobrazen\u00ed nehodnocen\u00fdch a odhl\u00e1\u0161en\u00fdch odpov\u011bd\u00ed se nepoda\u0159ilo na\u010d\u00edst.",
    "The following file types are not allowed: ": "N\u00e1sleduj\u00edc\u00ed typy soubor\u016f nejsou povolen\u00e9: ",
    "The maximum number files that can be saved is ": "Maxim\u00e1ln\u00ed po\u010det soubor\u016f, kter\u00e9 lze ulo\u017eit, je",
    "The onboarding service is temporarily unavailable. Please try again later.": "Slu\u017eba onboarding je do\u010dasn\u011b nedostupn\u00e1. Pros\u00edm zkuste to znovu pozd\u011bji.",
    "The server could not be contacted.": "Spojen\u00ed se serverem se nezda\u0159ilo.",
    "The staff assessment form could not be loaded.": "Nebylo mo\u017en\u00e9 na\u010d\u00edst formul\u00e1\u0159 pro hodnocen\u00ed u\u010ditel\u016f.",
    "The submission could not be removed from the grading pool.": "P\u0159\u00edsp\u011bvek se nepoda\u0159ilo odebrat z fondu hodnocen\u00ed.",
    "There are currently {stuck_learners} learners in the waiting state, meaning they have not yet met all requirements for Peer Assessment. ": "V sou\u010dasn\u00e9 dob\u011b je ve stavu \u010dek\u00e1n\u00ed {stuck_learners} student\u016f, co\u017e znamen\u00e1, \u017ee je\u0161t\u011b nesplnili v\u0161echny po\u017eadavky na Vz\u00e1jemn\u00e9 hodnocen\u00ed.",
    "There is no onboarding exam accessible to this user.": "Tento u\u017eivatel nem\u00e1 p\u0159\u00edstup k \u017e\u00e1dn\u00e9 vstupn\u00ed zkou\u0161ce.",
    "There is no onboarding exam related to this course id.": "S t\u00edmto ID kurzu nesouvis\u00ed \u017e\u00e1dn\u00e1 vstupn\u00ed zkou\u0161ka.",
    "This ORA has already been released. Changes will only affect learners making new submissions. Existing submissions will not be modified by this change.": "Tato ORA ji\u017e byla vyd\u00e1na. Zm\u011bny ovlivn\u00ed pouze studenty, kte\u0159\u00ed p\u0159id\u00e1vaj\u00ed nov\u00e9 p\u0159\u00edsp\u011bvky. St\u00e1vaj\u00edc\u00ed p\u0159\u00edsp\u011bvky nebudou touto zm\u011bnou upraveny.",
    "This assessment could not be submitted.": "Va\u0161e hodnocen\u00ed se nepoda\u0159ilo odeslat.",
    "This exam has a time limit associated with it.": "S touto zkou\u0161kou je spojen \u010dasov\u00fd limit.",
    "This feedback could not be submitted.": "Va\u0161i zp\u011btnou vazbu se nepoda\u0159ilo odeslat.",
    "This grade will be applied to all members of the team. Do you want to continue?": "Tato zn\u00e1mka bude aplikov\u00e1na na v\u0161echny \u010dleny t\u00fdmu. Chcete pokra\u010dovat?",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Seznam dostupn\u00fdch polo\u017eek %s. Jednotliv\u011b je lze vybrat tak, \u017ee na n\u011b v r\u00e1me\u010dku klepnete a pak klepnete na \u0161ipku \"Vybrat\" mezi r\u00e1me\u010dky.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Seznam vybran\u00fdch polo\u017eek %s. Jednotliv\u011b je lze odebrat tak, \u017ee na n\u011b v r\u00e1me\u010dku klepnete a pak klepnete na \u0161ipku \"Odebrat mezi r\u00e1me\u010dky.",
    "This problem could not be saved.": "Tato \u00faloha nem\u016f\u017ee b\u00fdt ulo\u017eena.",
    "This response could not be submitted.": "Va\u0161i odpov\u011b\u010f se nepoda\u0159ilo odeslat.",
    "This section could not be loaded.": "Tento odd\u00edl nebylo mo\u017en\u00e9 na\u010d\u00edst.",
    "Thumbnail view of ": "N\u00e1hled ",
    "Time Spent On Current Step": "\u010cas str\u00e1ven\u00fd na aktu\u00e1ln\u00edm kroku",
    "Timed Exam": "\u010casovan\u00e1 zkou\u0161ka",
    "Timed Out": "Vypr\u0161elo",
    "To pass this exam, you must complete the problems in the time allowed.": "Chcete-li tuto zkou\u0161ku slo\u017eit, mus\u00edte vy\u0159e\u0161it probl\u00e9my v povolen\u00e9m \u010dase.",
    "Today": "Dnes",
    "Tomorrow": "Z\u00edtra",
    "Total Responses": "Celkov\u00fd po\u010det odpov\u011bd\u00ed",
    "Training": "Tr\u00e9nink",
    "Type into this box to filter down the list of available %s.": "Chcete-li filtrovat ze seznamu dostupn\u00fdch polo\u017eek %s, za\u010dn\u011bte ps\u00e1t do tohoto pole.",
    "Unable to load": "Nelze na\u010d\u00edst",
    "Unexpected server error.": "Ne\u010dekan\u00e1 chyba serveru.",
    "Ungraded Practice Exam": "Neklasifikovan\u00e1 praktick\u00e1 zkou\u0161ka",
    "Unit Name": "N\u00e1zev jednotky",
    "Units": "Jednotky",
    "Unnamed Option": "Nepojmenovan\u00e1 mo\u017enost",
    "User lookup failed": "Hled\u00e1n\u00ed u\u017eivatele selhalo",
    "Username": "U\u017eivatelsk\u00e9 jm\u00e9no",
    "Verified": "Verifikovan\u00fd",
    "View and grade responses": "Zobrazit a ohodnotit odpov\u011bdi",
    "View my exam": "Zobrazit mou zkou\u0161ku",
    "Waiting": "\u010cek\u00e1n\u00ed",
    "Warning": "Varov\u00e1n\u00ed",
    "Yes, end my proctored exam": "Ano, ukon\u010dete moji proctorovanou zkou\u0161ku",
    "Yesterday": "V\u010dera",
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Assessment Steps tab.": "P\u0159idali jste krit\u00e9rium. Budete muset vybrat mo\u017enost pro krit\u00e9rium v kroku \u0160kolen\u00ed \u017e\u00e1ka. Chcete-li to prov\u00e9st, klepn\u011bte na kartu Kroky hodnocen\u00ed.",
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Smazali jste krit\u00e9rium. Krit\u00e9rium bylo odstran\u011bno z p\u0159\u00edklad\u016f odpov\u011bd\u00ed v kroku \u0160kolen\u00ed \u017e\u00e1ka.",
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Smazali jste v\u0161echny mo\u017enosti pro toto krit\u00e9rium. Krit\u00e9rium bylo odstran\u011bno z uk\u00e1zkov\u00fdch odpov\u011bd\u00ed v kroku \u0160kolen\u00ed \u017e\u00e1ka.",
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Smazali jste mo\u017enost. Tato mo\u017enost byla odstran\u011bna z krit\u00e9ria ve vzorov\u00fdch odpov\u011bd\u00edch v kroku \u0160kolen\u00ed \u017e\u00e1ka. Mo\u017en\u00e1 budete muset vybrat novou mo\u017enost pro krit\u00e9rium.",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Byla vybr\u00e1na operace, ale dosud nedo\u0161lo k ulo\u017een\u00ed zm\u011bn jednotliv\u00fdch pol\u00ed. Patrn\u011b vyu\u017eijete tla\u010d\u00edtko Prov\u00e9st sp\u00ed\u0161e ne\u017e tla\u010d\u00edtko Ulo\u017eit.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Byla vybr\u00e1na operace, ale dosud nedo\u0161lo k ulo\u017een\u00ed zm\u011bn jednotliv\u00fdch pol\u00ed. Ulo\u017e\u00edte klepnut\u00edm na tla\u010d\u00edtko OK. Pak bude t\u0159eba operaci spustit znovu.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "V jednotliv\u00fdch pol\u00edch jsou neulo\u017een\u00e9 zm\u011bny, kter\u00e9 budou ztraceny, pokud operaci provedete.",
    "You must provide a learner name.": "Mus\u00edte poskytnout jm\u00e9no studenta.",
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Chyst\u00e1te se odeslat svou odpov\u011b\u010f na tento \u00fakol. Po odesl\u00e1n\u00ed t\u00e9to odpov\u011bdi ji nelze zm\u011bnit ani odeslat novou odpov\u011b\u010f.",
    "Your file has been deleted or path has been changed: ": "V\u00e1\u0161 soubor byl smaz\u00e1n nebo byla zm\u011bn\u011bna cesta:",
    "Your recorded data should now be uploaded for review.": "Va\u0161e zaznamenan\u00e1 data by nyn\u00ed m\u011bla b\u00fdt nahr\u00e1na ke kontrole.",
    "a practice exam": "cvi\u010dnou zkou\u0161ku",
    "a proctored exam": "chr\u00e1n\u011bn\u00e1 zkou\u0161ka",
    "a timed exam": "\u010dasovan\u00e1 zkou\u0161ka",
    "abbrev. month April\u0004Apr": "Dub",
    "abbrev. month August\u0004Aug": "Srp",
    "abbrev. month December\u0004Dec": "Pro",
    "abbrev. month February\u0004Feb": "\u00dano",
    "abbrev. month January\u0004Jan": "Led",
    "abbrev. month July\u0004Jul": "\u010cvc",
    "abbrev. month June\u0004Jun": "\u010cvn",
    "abbrev. month March\u0004Mar": "B\u0159e",
    "abbrev. month May\u0004May": "Kv\u011b",
    "abbrev. month November\u0004Nov": "Lis",
    "abbrev. month October\u0004Oct": "\u0158\u00edj",
    "abbrev. month September\u0004Sep": "Z\u00e1\u0159",
    "active proctored exams": "aktivn\u00ed proktorovan\u00e9 zkou\u0161ky",
    "allowance_value": "allowance_value",
    "an onboarding exam": "vstupn\u00ed zkou\u0161ka",
    "could not determine the course_id": "nemohl ur\u010dit id_kurzu",
    "courses with active proctored exams": "kurzy s aktivn\u00ed dozorovanou zkou\u0161kou",
    "error count: ": "po\u010det chyb:",
    "internally reviewed": "intern\u011b p\u0159ezkoum\u00e1no",
    "one letter Friday\u0004F": "P",
    "one letter Monday\u0004M": "P",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "N",
    "one letter Thursday\u0004T": "\u010c",
    "one letter Tuesday\u0004T": "\u00da",
    "one letter Wednesday\u0004W": "S",
    "user_info": "user_info",
    "you have less than a minute remaining": "zb\u00fdv\u00e1 v\u00e1m m\u00e9n\u011b ne\u017e minuta",
    "you have {remaining_time} remaining": "zb\u00fdv\u00e1 v\u00e1m {remaining_time}",
    "you will have ": "budete m\u00edt",
    "your course": "v\u00e1\u0161 kurz",
    "{num_of_hours} hour": "{num_of_hours} hodin",
    "{num_of_hours} hours": "{num_of_hours} hodin",
    "{num_of_minutes} minute": "{num_of_minutes} minut",
    "{num_of_minutes} minutes": "{num_of_minutes} minut"
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
    "DATETIME_FORMAT": "j. E Y G:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H.%M",
      "%d.%m.%Y %H:%M",
      "%d. %m. %Y %H:%M:%S",
      "%d. %m. %Y %H:%M:%S.%f",
      "%d. %m. %Y %H.%M",
      "%d. %m. %Y %H:%M",
      "%Y-%m-%d %H.%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j. E Y",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y",
      "%d.%m.%y",
      "%d. %m. %Y",
      "%d. %m. %y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j. F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y G:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "G:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H.%M",
      "%H:%M",
      "%H:%M:%S.%f"
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

