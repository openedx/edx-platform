

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n > 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "\n\nThis email is to let you know that the status of your proctoring session review for %(exam_name)s in\n<a href=\"%(course_url)s\">%(course_name)s </a> is %(status)s. If you have any questions about proctoring,\ncontact %(platform)s support at %(contact_email)s.\n\n": "\n\nCe courriel a pour but de vous informer que le statut de votre examen de session de surveillance pour %(exam_name)s pour\n<a href=\"%(course_url)s\">%(course_name)s </a> est %(status)s. Si vous avez des questions sur la surveillance,\ncontactez le support %(platform)s au %(contact_email)s.\n\n", 
    "\n                    Make sure you are on a computer with a webcam, and that you have valid photo identification\n                    such as a driver's license or passport, before you continue.\n                ": "\n                    Assurez-vous que vous \u00eates sur un ordinateur \u00e9quip\u00e9 d'une webcam et que vous poss\u00e9dez une pi\u00e8ce d'identit\u00e9 avec photo valide\n                    comme un permis de conduire ou un passeport, avant de continuer.\n                ", 
    "\n                    Your verification attempt failed. Please read our guidelines to make\n                    sure you understand the requirements for successfully completing verification,\n                    then try again.\n                ": "\n                    Votre tentative de v\u00e9rification a \u00e9chou\u00e9. S'il vous pla\u00eet lire nos lignes directrices pour \u00eatre\n                    certain que vous comprenez les exigences pour r\u00e9ussir votre v\u00e9rification ,\n                    et essayez de nouveau.\n                ", 
    "\n                    Your verification has expired. You must successfully complete a new identity verification\n                    before you can start the proctored exam.\n                ": "\n                    Votre v\u00e9rification a expir\u00e9. Vous devez r\u00e9ussir une nouvelle v\u00e9rification d'identit\u00e9\n                    avant de pouvoir commencer l'examen surveill\u00e9.\n                ", 
    "\n                    Your verification is pending. Results should be available 2-3 days after you\n                    submit your verification.\n                ": "\n                    Votre v\u00e9rification est en attente. Les r\u00e9sultats devraient \u00eatre disponibles 2-3 jours apr\u00e8s\n                    avoir soumis votre v\u00e9rification.\n                ", 
    "\n                Complete your verification before starting the proctored exam.\n            ": "\nTerminez votre v\u00e9rification avant de commencer l'examen surveill\u00e9.", 
    "\n                You must successfully complete identity verification before you can start the proctored exam.\n            ": "\nVous devez r\u00e9ussir la v\u00e9rification de l'identit\u00e9 avant de pouvoir lancer l'examen supervis\u00e9.", 
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\n            Ne fermez pas cette fen\u00eatre avant la fin de votre examen. Si vous fermez cette fen\u00eatre, votre session de surveillance se terminera et vous ne r\u00e9ussirez pas \u00e0 passer l'examen surveill\u00e9.\n          ", 
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\n            Retournez \u00e0 la fen\u00eatre du cours %(platform_name)s pour commencer votre examen. Lorsque vous aurez termin\u00e9 votre examen et\n            l'avoir marqu\u00e9 comme complet, vous pourrez fermer cette fen\u00eatre pour mettre fin \u00e0 la session de surveillance\n            et t\u00e9l\u00e9chargez vos donn\u00e9es de session de surveillance pour revue.\n          ", 
    "\n          3. When you have finished setting up proctoring, start the exam.\n        ": "\n3. Lorsque vous avez termin\u00e9 la configuration de la surveillance, commencez l'examen.", 
    "\n          Start my exam\n        ": "\nCommencer mon examen", 
    "\n        &#8226; When you start your exam you will have %(total_time)s to complete it. </br>\n        &#8226; You cannot stop the timer once you start. </br>\n        &#8226; If time expires before you finish your exam, your completed answers will be\n                submitted for review. </br>\n      ": "\n        &#8226; Lorsque vous commencerez votre examen, vous aurez %(total_time)s afin de le compl\u00e9ter. </br>\n        &#8226; Vous ne pouvez pas arr\u00eater le chronom\u00e8tre une fois que vous avez commenc\u00e9. </br>\n        &#8226; Si le temps expire avant la fin de votre examen, les r\u00e9ponses compl\u00e9t\u00e9es seront\n                soumises pour revue. </br>\n      ", 
    "\n        1. Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n      ": "\n        1. Copiez ce code d'examen unique. Vous serez invit\u00e9 \u00e0 coller ce code plus tard avant de commencer l'examen.\n      ", 
    "\n        2. Follow the link below to set up proctoring.\n      ": "\n2. Suivez le lien ci-dessous pour configurer la surveillance.", 
    "\n        A new window will open. You will run a system check before downloading the proctoring application.\n      ": "\n        Une nouvelle fen\u00eatre va s'ouvrir. Vous allez effectuer une v\u00e9rification du syst\u00e8me avant de t\u00e9l\u00e9charger l'application de surveillance.\n      ", 
    "\n        About Proctored Exams\n        ": "\n\u00c0 propos des examens surveill\u00e9s", 
    "\n        After the due date has passed, you can review the exam, but you cannot change your answers.\n      ": "\nUne fois la date d'\u00e9ch\u00e9ance pass\u00e9e, vous pouvez passer en revue l'examen, mais vous ne pouvez pas modifier vos r\u00e9ponses.", 
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n\u00cates-vous s\u00fbr de vouloir passer cet examen sans surveillance?", 
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\n        En raison de pr\u00e9requis insatisfaits, vous ne pouvez passer cet examen que sans surveillance.\n      ", 
    "\n        I am not interested in academic credit.\n      ": "\nJe ne suis pas int\u00e9ress\u00e9 par un cr\u00e9dit acad\u00e9mique.", 
    "\n        I am ready to start this timed exam.\n      ": "\nJe suis pr\u00eat \u00e0 commencer cet examen chronom\u00e9tr\u00e9.", 
    "\n        If you take this exam without proctoring, you will <strong> no longer be eligible for academic credit. </strong>\n      ": "\n        Si vous passez cet examen sans surveillance, vous ne serez plus <strong> admissible au cr\u00e9dit d'\u00e9tudes. </strong>\n      ", 
    "\n        No, I want to continue working.\n      ": "\nNon, je veux continuer \u00e0 travailler.", 
    "\n        No, I'd like to continue working\n      ": "\nNon, je veux continuer \u00e0 travailler", 
    "\n        Select the exam code, then copy it using Command+C (Mac) or Control+C (Windows).\n      ": "\n       S\u00e9lectionnez le code d'examen, puis copiez-le en utilisant Command+C (Mac) ou Control+C (Windows).\n      ", 
    "\n        The time allotted for this exam has expired. Your exam has been submitted and any work you completed will be graded.\n      ": "\nLe temps allou\u00e9 pour cet examen a expir\u00e9. Votre examen a \u00e9t\u00e9 soumis et tout travail que vous avez termin\u00e9 sera \u00e9valu\u00e9.", 
    "\n        You have submitted your timed exam.\n      ": "\nVous avez soumis votre examen chronom\u00e9tr\u00e9.", 
    "\n        You will be asked to verify your identity as part of the proctoring exam set up.\n        Make sure you are on a computer with a webcam, and that you have valid photo identification\n        such as a driver's license or passport, before you continue.\n      ": "\n        Vous serez invit\u00e9 \u00e0 v\u00e9rifier votre identit\u00e9 dans le cadre de la mise en place de l'examen de surveillance.\n        Assurez-vous que vous \u00eates sur un ordinateur \u00e9quip\u00e9 d'une webcam et que vous poss\u00e9dez une pi\u00e8ce d'identit\u00e9 avec photo valide\n        comme un permis de conduire ou un passeport, avant de continuer.\n      ", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.\n      ": "\n        Vous serez guid\u00e9 \u00e0 travers les \u00e9tapes pour mettre en place un logiciel de surveillance en ligne et effectuer diverses v\u00e9rifications.\n      ", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.</br>\n      ": "\nVous serez guid\u00e9 par des \u00e9tapes pour configurer un logiciel de surveillance en ligne et effectuer divers contr\u00f4les</br>", 
    "\n      &#8226; After you quit the proctoring session, the recorded data is uploaded for review. </br>\n      &#8226; Proctoring results are usually available within 5 business days after you submit your exam.\n    ": "\n      &#8226; Apr\u00e8s avoir quitt\u00e9 la session de surveillance, les donn\u00e9es enregistr\u00e9es sont t\u00e9l\u00e9charg\u00e9es pour r\u00e9vision.</br>\n      &#8226; Les r\u00e9sultats de la surveillance sont g\u00e9n\u00e9ralement disponibles dans les 5 jours ouvrables apr\u00e8s la soumission de votre examen.\n    ", 
    "\n      A technical error has occurred with your proctored exam. To resolve this problem, contact\n      <a href=\"mailto:%(tech_support_email)s\">technical support</a>. All exam data, including answers\n      for completed problems, has been lost. When the problem is resolved you will need to restart\n      the exam and complete all problems again.\n    ": "\n     Une erreur technique s'est produite avec votre examen surveill\u00e9. Pour r\u00e9soudre ce probl\u00e8me, contactez le\n      <a href=\"mailto:%(tech_support_email)s\">support technnique</a>. Toutes les donn\u00e9es d'examen, y compris les r\u00e9ponses\n      pour les probl\u00e8mes termin\u00e9s, ont \u00e9t\u00e9 perdues. Lorsque le probl\u00e8me est r\u00e9solu, vous devrez red\u00e9marrer\n      l'examen et compl\u00e9ter tous les probl\u00e8mes \u00e0 nouveau.\n    ", 
    "\n      After the due date for this exam has passed, you will be able to review your answers on this page.\n    ": "\n      Apr\u00e8s que la date d'\u00e9ch\u00e9ance pour cet examen soit pass\u00e9e, vous serez en mesure de revoir vos r\u00e9ponses sur cette page.\n    ", 
    "\n      After you submit your exam, your exam will be graded.\n    ": "\nApr\u00e8s avoir soumis votre examen, votre examen sera not\u00e9.", 
    "\n      After you submit your exam, your responses are graded and your proctoring session is reviewed.\n      You might be eligible to earn academic credit for this course if you complete all required exams\n      as well as achieve a final grade that meets credit requirements for the course.\n    ": "\n      Apr\u00e8s avoir soumis votre examen, vos r\u00e9ponses sont not\u00e9es et votre session de surveillance est examin\u00e9e.\n      Vous pourriez \u00eatre admissible \u00e0 un cr\u00e9dit acad\u00e9mique pour ce cours si vous r\u00e9pondez \u00e0 tous les examens requis\n      et avez atteint une note finale qui r\u00e9pond aux exigences de cr\u00e9dit pour le cours.\n    ", 
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n\u00cates-vous certain de vouloir soumettre votre examen chronom\u00e9tr\u00e9?", 
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n\u00cates-vous certain de vouloir terminer votre examen supervis\u00e9?", 
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\n      Parce que la date d'\u00e9ch\u00e9ance est pass\u00e9e, vous n'\u00eates plus en mesure de passer cet examen.\n    ", 
    "\n      Error with proctored exam\n    ": "\nErreur avec l'examen surveill\u00e9", 
    "\n      Follow these instructions\n    ": "\nSuivez ces instructions", 
    "\n      Follow these steps to set up and start your proctored exam.\n    ": "\nSuivez ces \u00e9tapes pour configurer et d\u00e9marrer votre examen surveill\u00e9.", 
    "\n      Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n      on your grade in the course.\n    ": "\n      Familiarisez-vous avec la surveillance pour les vrais examens plus tard dans le cours. Cet examen pratique n'a aucun impact\n      sur votre note au cours.\n    ", 
    "\n      If the proctoring software window is still open, you can close it now. Confirm that you want to quit the application when you are prompted.\n    ": "\n      Si la fen\u00eatre du logiciel de surveillance est toujours ouverte, vous pouvez la fermer maintenant. Confirmez que vous voulez quitter l'application lorsque vous y \u00eates invit\u00e9.\n    ", 
    "\n      If you have concerns about your proctoring session results, contact your course team.\n    ": "\n      Si vous avez des inqui\u00e9tudes concernant les r\u00e9sultats de votre session de surveillance, contactez votre \u00e9quipe p\u00e9dagogique.\n    ", 
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\n     Si vous avez un handicap,\n      vous pourriez \u00eatre admissible \u00e0 une allocation de temps suppl\u00e9mentaire pour les examens chronom\u00e9tr\u00e9s.\n      Demandez \u00e0 votre \u00e9quipe p\u00e9dagogique des informations sur les d\u00e9lais suppl\u00e9mentaires.\n    ", 
    "\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\nSi vous avez des questions sur l'\u00e9tat des r\u00e9sultats de votre examen surveill\u00e9, contactez le support %(platform_name)s.", 
    "\n      If you have questions about the status of your requirements for course credit, contact %(platform_name)s Support.\n    ": "\n      Si vous avez des questions sur le statut de vos exigences pour les cr\u00e9dits de cours, contactez le support %(platform_name)s.\n    ", 
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\n      Assurez-vous que vous avez s\u00e9lectionn\u00e9 \"Soumettre\" pour chaque probl\u00e8me avant de soumettre votre examen.\n    ", 
    "\n      Practice exams do not affect your grade or your credit eligibility.\n      You have completed this practice exam and can continue with your course work.\n    ": "\n      Les examens de pratique n'ont aucune incidence sur votre note ou votre admissibilit\u00e9 au cr\u00e9dit.\n      Vous avez termin\u00e9 cet examen pratique et pouvez continuer votre travail de cours.\n    ", 
    "\n      The due date for this exam has passed\n    ": "\nLa date d'\u00e9ch\u00e9ance pour cet examen est pass\u00e9e", 
    "\n      There was a problem with your practice proctoring session\n    ": "\nIl y a eu un probl\u00e8me avec votre s\u00e9ance d'examen surveill\u00e9 de pratique", 
    "\n      This exam is proctored\n    ": "\nCet examen est surveill\u00e9", 
    "\n      To be eligible for course credit or for a MicroMasters credential, you must pass the proctoring review for this exam.\n    ": "\n      Pour \u00eatre admissible au cr\u00e9dit de cours ou \u00e0 un titre de comp\u00e9tence MicroMasters, vous devez r\u00e9ussir l'examen de surveillance pour cet examen.\n    ", 
    "\n      To view your exam questions and responses, select <strong>View my exam</strong>. The exam's review status is shown in the left navigation pane.\n    ": "\n      Pour afficher vos questions et r\u00e9ponses d'examen, s\u00e9lectionnez<strong>Voir mon examen</strong>. L'\u00e9tat de revue de l'examen est affich\u00e9 dans le volet de navigation de gauche.\n    ", 
    "\n      Try a proctored exam\n    ": "\nEssayez un examen surveill\u00e9", 
    "\n      View your credit eligibility status on your <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\nConsultez votre statut d'admissibilit\u00e9 au cr\u00e9dit sur votre page de <a href=\"%(progress_page_url)s\">Progression</a>.", 
    "\n      Yes, end my proctored exam\n    ": "\nOui, terminez mon examen surveill\u00e9", 
    "\n      Yes, submit my timed exam.\n    ": "\nOui, soumettez mon examen chronom\u00e9tr\u00e9.", 
    "\n      You are eligible to purchase academic credit for this course if you complete all required exams\n      and also achieve a final grade that meets the credit requirements for the course.\n    ": "\n      Vous avez droit \u00e0 un cr\u00e9dit acad\u00e9mique pour ce cours si vous avez termin\u00e9 tous les examens requis\n      et avez atteint une note finale qui r\u00e9pond aux exigences de cr\u00e9dit pour le cours.\n    ", 
    "\n      You are no longer eligible for academic credit for this course, regardless of your final grade.\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\n      Vous n'\u00eates plus admissible au cr\u00e9dit d'\u00e9tudes pour ce cours, peu importe votre note finale.\n     Si vous avez des questions sur l'\u00e9tat de vos r\u00e9sultats d'examens surveill\u00e9s, contactez le support %(platform_name)s.\n    ", 
    "\n      You have submitted this practice proctored exam\n    ": "\nVous avez soumis cet examen surveill\u00e9 de pratique.", 
    "\n      You have submitted this proctored exam for review\n    ": "\nVous avez soumis cet examen surveill\u00e9 pour r\u00e9vision", 
    "\n      Your grade for this timed exam will be immediately available on the <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\nVotre note pour cet examen chronom\u00e9tr\u00e9 sera imm\u00e9diatement disponible sur la page <a href=\"%(progress_page_url)s\">Progression</a>.", 
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\nLes r\u00e9sultats de votre examen surveill\u00e9 de pratique : <b class=\"failure\"> Insatisfaisant </b>", 
    "\n      Your proctoring session ended before you completed this practice exam.\n      You can retry this practice exam if you had problems setting up the online proctoring software.\n    ": "\n      Votre session de surveillance s'est termin\u00e9e avant que vous ayez termin\u00e9 cet examen de pratique.\n      Vous pouvez r\u00e9essayer cet examen si vous avez eu des probl\u00e8mes lors de la configuration du logiciel de surveillance en ligne.\n    ", 
    "\n      Your proctoring session was reviewed and did not pass requirements\n    ": "\nVotre s\u00e9ance surveill\u00e9e a \u00e9t\u00e9 examin\u00e9e et n'a r\u00e9pondue aux exigences", 
    "\n      Your proctoring session was reviewed and passed all requirements\n    ": "\nVotre s\u00e9ance surveill\u00e9e a \u00e9t\u00e9 examin\u00e9e et a r\u00e9pondu \u00e0 toutes les exigences", 
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n%(exam_name)s est un examen chronom\u00e9tr\u00e9 (%(total_time)s)", 
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\n    Les pr\u00e9requis suivants sont dans un \u00e9tat <strong>en attente </strong>et doivent \u00eatre compl\u00e9t\u00e9s avec succ\u00e8s avant de pouvoir proc\u00e9der:\n    ", 
    "\n    You can take this exam with proctoring only when all prerequisites have been successfully completed. Check your <a href=\"%(progress_page_url)s\">Progress</a>  page to see if prerequisite results have been updated. You can also take this exam now without proctoring, but you will not be eligible for credit.\n    ": "\n   Vous pouvez passer cet examen avec surveillance uniquement lorsque tous les pr\u00e9requis ont \u00e9t\u00e9 compl\u00e9t\u00e9s avec succ\u00e8s. Consultez votre page de<a href=\"%(progress_page_url)s\">Progression</a> pour voir si les r\u00e9sultats pr\u00e9requis ont \u00e9t\u00e9 mis \u00e0 jour. Vous pouvez \u00e9galement passer cet examen sans surveillance, mais vous ne pourrez pas obtenir de cr\u00e9dit.\n    ", 
    "\n    You did not satisfy the following prerequisites:\n    ": "\nVous n'avez pas satisfait aux conditions pr\u00e9alables suivantes:", 
    "\n    You did not satisfy the requirements for taking this exam with proctoring, and are not eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements and your status for each.\n    ": "\n    Vous n'avez pas satisfait aux exigences pour passer cet examen avec la surveillance, et n'\u00eates pas admissible \u00e0 un cr\u00e9dit. Voir votre page de <a href=\"%(progress_page_url)s\">Progression</a> pour une liste d'exigences et votre statut pour chacunes d'elles.\n    ", 
    "\n    You have not completed the prerequisites for this exam. All requirements must be satisfied before you can take this proctored exam and be eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements in the order that they must be completed.\n    ": "\n    Vous n'avez pas rempli les pr\u00e9requis pour cet examen. Toutes les exigences doivent \u00eatre satisfaites avant de pouvoir passer cet examen surveill\u00e9 et \u00eatre admissible \u00e0 un cr\u00e9dit. Consultez votre page de <a href=\"%(progress_page_url)s\">Progression</a> pour une liste d'exigences et l'ordre dans lequel elles doivent \u00eatre compl\u00e9t\u00e9es.\n    ", 
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": " \u00c0 partir de ce moment, vous devez suivre les <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">r\u00e8gles de surveillance en ligne</a> afin de passer la revue de surveillance pour votre examen. ", 
    " Your Proctoring Session Has Started ": "Votre session surveill\u00e9e a commenc\u00e9e", 
    " and {num_of_minutes} minute": "ajouter {num_of_minutes} minute", 
    " and {num_of_minutes} minutes": "ajouter {num_of_minutes} minutes", 
    " to complete and submit the exam.": "pour compl\u00e9ter et soumettre l'examen.", 
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s sur %(cnt)s s\u00e9lectionn\u00e9", 
      "%(sel)s sur %(cnt)s s\u00e9lectionn\u00e9s"
    ], 
    "(required):": "(requis) :", 
    "6 a.m.": "6:00", 
    "6 p.m.": "18:00", 
    "Additional Time (minutes)": "Temps additionnel (minutes)", 
    "After you select ": "Apr\u00e8s avoir s\u00e9lectionn\u00e9", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Apr\u00e8s avoir t\u00e9l\u00e9vers\u00e9 de nouveaux fichiers, tous vos fichiers pr\u00e9c\u00e9demment t\u00e9l\u00e9vers\u00e9s seront \u00e9cras\u00e9s. Voulez-vous poursuivre?", 
    "All Unreviewed": "Tous non r\u00e9vis\u00e9s", 
    "All Unreviewed Failures": "Tous les \u00e9checs non r\u00e9vis\u00e9s", 
    "April": "Avril", 
    "Assessment": "\u00c9valuation", 
    "Assessments": "\u00c9valuations", 
    "August": "Ao\u00fbt", 
    "Available %s": "%s disponible(s)", 
    "Back to Full List": "Retour \u00e0 la liste compl\u00e8te", 
    "Block view is unavailable": "La vue en bloc est indisponible.", 
    "Can I request additional time to complete my exam?": "Puis-je demander du temps suppl\u00e9mentaire pour terminer mon examen?", 
    "Cancel": "Annuler", 
    "Cannot Start Proctored Exam": "Impossible de lancer l'examen surveill\u00e9", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Les modifications apport\u00e9es aux \u00e9tapes qui ne sont pas s\u00e9lectionn\u00e9s dans le cadre du devoir ne seront pas sauvegard\u00e9es.", 
    "Choose": "Choisir", 
    "Choose a Date": "Choisir une date", 
    "Choose a Time": "Choisir une heure", 
    "Choose a time": "Choisir une heure", 
    "Choose all": "Tout choisir", 
    "Chosen %s": "Choix des \u00ab\u00a0%s \u00bb", 
    "Click to choose all %s at once.": "Cliquez pour choisir tous les \u00ab\u00a0%s\u00a0\u00bb en une seule op\u00e9ration.", 
    "Click to remove all chosen %s at once.": "Cliquez pour enlever tous les \u00ab\u00a0%s\u00a0\u00bb en une seule op\u00e9ration.", 
    "Close": "Fermer", 
    "Continue Exam Without Proctoring": "Continuer l'examen sans surveillance", 
    "Continue to Verification": "Continuer vers la v\u00e9rification", 
    "Continue to my practice exam": "Continuer \u00e0 mon examen de pratique", 
    "Continue to my proctored exam. I want to be eligible for credit.": "Continuer vers mon examen surveill\u00e9. Je veux \u00eatre admissible au cr\u00e9dit.", 
    "Could not retrieve download url.": "mpossible de r\u00e9cup\u00e9rer le url de t\u00e9l\u00e9chargement.", 
    "Could not retrieve upload url.": "Impossible de r\u00e9cup\u00e9rer le url de t\u00e9l\u00e9versement.", 
    "Couldn't Save This Assignment": "Impossible de sauvegarder le devoir", 
    "Course Id": "ID de cours", 
    "Created": "Cr\u00e9\u00e9e", 
    "Criterion Added": "Crit\u00e8re ajout\u00e9", 
    "Criterion Deleted": "Crit\u00e8re supprim\u00e9", 
    "December": "D\u00e9cembre", 
    "Declined": "Refus\u00e9", 
    "Delete student '<%- student_id %>'s state on problem '<%- problem_id %>'?": "Supprimer l'\u00e9tat de l'\u00e9tudiant '<%- student_id %>' pour le probl\u00e8me '<%- problem_id %>'?", 
    "Describe ": "D\u00e9crire", 
    "Do you want to upload your file before submitting?": "Voulez-vous t\u00e9l\u00e9verser votre fichier avant de le soumettre?", 
    "Doing so means that you are no longer eligible for academic credit.": "Cela signifie que vous n'\u00eates plus admissible au cr\u00e9dit acad\u00e9mique.", 
    "Download Software Clicked": "T\u00e9l\u00e9chargement du logiciel cliqu\u00e9", 
    "Error": "Erreur", 
    "Error deleting student '<%- student_id %>'s state on problem '<%- problem_id %>'. Make sure that the problem and student identifiers are complete and correct.": "Erreur lors de la suppression de l'\u00e9tat de l'\u00e9tudiant '<%- student_id %>' pour le probl\u00e8me '<%- problem_id %>'. V\u00e9rifiez qu'il n'y ait pas d'erreur dans les identifiants du probl\u00e8me et de l'\u00e9tudiant.", 
    "Error getting task history for problem '<%- problem_id %>' and student '<%- student_id %>'. Make sure that the problem and student identifiers are complete and correct.": "Erreur dans la r\u00e9cup\u00e9ration de l'historique du probl\u00e8me '<%- problem_id %>' pour l'\u00e9tudiant '<%- student_id %>'. V\u00e9rifiez qu'il n'y ait pas d'erreur dans les identifiants du probl\u00e8me et de l'\u00e9tudiant.", 
    "Error getting the number of ungraded responses": "Erreur d'obtention du nombre de r\u00e9ponses non not\u00e9s", 
    "Error resetting problem attempts for problem '<%= problem_id %>' and student '<%- student_id %>'. Make sure that the problem and student identifiers are complete and correct.": "Erreur dans la r\u00e9initialisation des essais pour le probl\u00e8me '<%= problem_id %>' et l'\u00e9tudiant '<%- student_id %>'. V\u00e9rifiez qu'il n'y ait pas d'erreur dans les identifiants du probl\u00e8me et de l'\u00e9tudiant.", 
    "Error starting a task to reset attempts for all students on problem '<%- problem_id %>'. Make sure that the problem identifier is complete and correct.": "Erreur dans la r\u00e9initialisation des essais de tous les \u00e9tudiants pour le probl\u00e8me '<%- problem_id %>'. V\u00e9rifiez que l'identifiant du probl\u00e8me est complet et correct.", 
    "Failed Proctoring": "A \u00e9chou\u00e9 la surveillance", 
    "February": "F\u00e9vrier", 
    "Feedback available for selection.": "R\u00e9troaction disponible pour la s\u00e9lection.", 
    "File size must be 10MB or less.": "La taille du fichier doit \u00eatre de 10 Mo ou moins.", 
    "File type is not allowed.": "Format de fichier non permis.", 
    "File types can not be empty.": "Les formats de fichiers ne peuvent \u00eatre vides.", 
    "Filter": "Filtrer", 
    "Final Grade Received": "Note finale re\u00e7ue", 
    "Go Back": "Retour", 
    "Heading 3": "Titre 3", 
    "Heading 4": "Titre 4", 
    "Heading 5": "Titre 5", 
    "Heading 6": "Titre 6", 
    "Hide": "Masquer", 
    "I am ready to start this timed exam,": "Je suis pr\u00eat \u00e0 commencer cet examen chronom\u00e9tr\u00e9,", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Si vous quittez cette page sans soumettre votre r\u00e9ponse, vous perdrez tout travail que vous avez fait sur la r\u00e9ponse.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Si vous quittez cette page sans soumettre votre \u00e9valuation des pairs, vous perdrez tout travail que vous avez fait.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Si vous quittez cette page sans soumettre votre auto-\u00e9valuation, vous perdrez tout travail que vous avez fait.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Si vous quittez cette page sans soumettre votre \u00e9valuation du personnel, vous perdrez tout travail que vous avez fait.", 
    "Is Sample Attempt": "Tentative d'\u00e9chantillonnage", 
    "January": "Janvier", 
    "July": "Juillet", 
    "June": "Juin", 
    "List of Open Assessments is unavailable": "La liste des \u00e9valuations ouvertes est indisponible", 
    "March": "Mars", 
    "May": "Mai", 
    "Midnight": "Minuit", 
    "Must be a Staff User to Perform this request.": "Doit \u00eatre un membre de l'\u00e9quipe p\u00e9dagogique pour effectuer cette requ\u00eate.", 
    "Noon": "Midi", 
    "Not Selected": "Non s\u00e9lectionn\u00e9", 
    "Note: You are %s hour ahead of server time.": [
      "Note\u00a0: l'heure du serveur pr\u00e9c\u00e8de votre heure de %s heure.", 
      "Note\u00a0: l'heure du serveur pr\u00e9c\u00e8de votre heure de %s heures."
    ], 
    "Note: You are %s hour behind server time.": [
      "Note\u00a0: votre heure pr\u00e9c\u00e8de l'heure du serveur de %s heure.", 
      "Note\u00a0: votre heure pr\u00e9c\u00e8de l'heure du serveur de %s heures."
    ], 
    "November": "Novembre", 
    "Now": "Maintenant", 
    "October": "Octobre", 
    "One or more rescheduling tasks failed.": "Une ou plusieurs t\u00e2ches de replanification ont \u00e9chou\u00e9.", 
    "Option Deleted": "Option supprim\u00e9e", 
    "Paragraph": "Paragraphe", 
    "Passed Proctoring": "A pass\u00e9 la surveillance", 
    "Peer": "Pair", 
    "Pending Session Review": "Examen de la session en attente", 
    "Please correct the outlined fields.": "S'il vous pla\u00eet corriger les champs d\u00e9crits.", 
    "Please wait": "Veuillez patienter", 
    "Practice Exam Completed": "Examen de pratique termin\u00e9", 
    "Practice Exam Failed": "Examen de pratique \u00e9chou\u00e9", 
    "Preformatted": "Pr\u00e9format\u00e9", 
    "Proctored Option Available": "Option surveill\u00e9e disponible", 
    "Proctored Option No Longer Available": "L'option surveill\u00e9e n'est plus disponible", 
    "Proctoring Session Results Update for {course_name} {exam_name}": "Mise \u00e0 jour pour des r\u00e9sultats de la session surveill\u00e9e pour {course_name} {exam_name}", 
    "Ready To Start": "Pr\u00eat \u00e0 commencer", 
    "Ready To Submit": "Pr\u00eat \u00e0 soumettre", 
    "Rejected": "Rejet\u00e9", 
    "Remove": "Enlever", 
    "Remove all": "Tout enlever", 
    "Retry Verification": "R\u00e9essayer la v\u00e9rification", 
    "Review Policy Exception": "Examen de la politique d'exception", 
    "Saving...": "Sauvegarde...", 
    "Second Review Required": "Deuxi\u00e8me examen requis", 
    "Self": "Auto", 
    "September": "Septembre", 
    "Server error.": "Erreur de serveur.", 
    "Show": "Afficher", 
    "Staff": "\u00c9quipe p\u00e9dagogique", 
    "Start Proctored Exam": "D\u00e9marrer l'examen surveill\u00e9", 
    "Start System Check": "D\u00e9marrer la v\u00e9rification du syst\u00e8me", 
    "Started": "D\u00e9but\u00e9", 
    "Started rescore problem task for problem '<%- problem_id %>' and student '<%- student_id %>'. Click the 'Show Task Status' button to see the status of the task.": "Le recalcul du score du probl\u00e8me '<%- problem_id %>' de l'\u00e9tudiant '<%- student_id %>' a commenc\u00e9. Cliquez sur le bouton 'Montrer l'\u00e9tat de la t\u00e2che' pour voir l'\u00e9tat de la t\u00e2che.", 
    "Status of Your Response": "\u00c9tat de votre r\u00e9ponse", 
    "Submitted": "Soumis", 
    "Successfully started task to reset attempts for problem '<%- problem_id %>'. Click the 'Show Task Status' button to see the status of the task.": "D\u00e9marrage de la t\u00e2che consistant \u00e0 r\u00e9initialiser les tentatives pour le probl\u00e8me '<%- problem_id %>' effectu\u00e9 avec succ\u00e8s. Cliquez sur le bouton 'Montrer l'\u00e9tat de la t\u00e2che' pour voir l'\u00e9tat de la t\u00e2che.", 
    "Take this exam without proctoring.": "Prenez cet examen sans surveillance.", 
    "Taking As Open Exam": "Prendre comme examen ouvert", 
    "Taking As Proctored Exam": "Prendre comme examen surveill\u00e9", 
    "Taking as Proctored": "Prendre comme examen surveill\u00e9", 
    "The display of ungraded and checked out responses could not be loaded.": "L'affichage des r\u00e9ponses non not\u00e9es et des r\u00e9ponses s\u00e9lectionn\u00e9es ne peuvent \u00eatre charg\u00e9es.", 
    "The following file types are not allowed: ": "Les formats de fichiers suivants ne sont pas permis : ", 
    "The server could not be contacted.": "Le serveur n'a pu \u00eatre rejoint.", 
    "The staff assessment form could not be loaded.": "Le formulaire d'\u00e9valuation du personnel ne peut \u00eatre charg\u00e9.", 
    "The submission could not be removed from the grading pool.": "La soumission n'a pas pu \u00eatre retir\u00e9 du bassin de notation.", 
    "This assessment could not be submitted.": "Ce devoir n'a pu \u00eatre soumis.", 
    "This exam has a time limit associated with it.": "Cet examen a une limite de temps qui lui est associ\u00e9e.", 
    "This feedback could not be submitted.": "Ce commentaire n'a pu \u00eatre soumis.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Ceci est une liste des \u00ab\u00a0%s\u00a0\u00bb disponibles. Vous pouvez en choisir en les s\u00e9lectionnant dans la zone ci-dessous, puis en cliquant sur la fl\u00e8che \u00ab\u00a0Choisir\u00a0\u00bb entre les deux zones.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Ceci est la liste des \u00ab\u00a0%s\u00a0\u00bb choisi(e)s. Vous pouvez en enlever en les s\u00e9lectionnant dans la zone ci-dessous, puis en cliquant sur la fl\u00e8che \u00ab Enlever \u00bb entre les deux zones.", 
    "This problem could not be saved.": "Ce probl\u00e8me n'a pu \u00eatre sauvegard\u00e9.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "Cet exercice a d\u00e9j\u00e0 \u00e9t\u00e9 publi\u00e9. Toute modification ne sera applicable que pour les devoirs futurs.", 
    "This response could not be saved.": "Cette r\u00e9ponse n'a pu \u00eatre sauvegard\u00e9e.", 
    "This response could not be submitted.": "Cette r\u00e9ponse n'a pu \u00eatre soumise.", 
    "This response has been saved but not submitted.": "Cette r\u00e9ponse a \u00e9t\u00e9 sauvegard\u00e9e mais n'a pas \u00e9t\u00e9 soumise.", 
    "This response has not been saved.": "Cette r\u00e9ponse n'a pas \u00e9t\u00e9 sauvegard\u00e9e.", 
    "This section could not be loaded.": "Cette section ne peut \u00eatre charg\u00e9e.", 
    "Thumbnail view of ": "Vue miniature de", 
    "Timed Exam": "Examen minut\u00e9", 
    "Timed Out": "Temps expir\u00e9", 
    "To pass this exam, you must complete the problems in the time allowed.": "Pour passer cet examen, vous devez compl\u00e9ter les probl\u00e8mes dans le temps imparti.", 
    "Today": "Aujourd'hui", 
    "Tomorrow": "Demain", 
    "Total Responses": "R\u00e9ponses totales", 
    "Training": "Entra\u00eenement", 
    "Try this practice exam again": "R\u00e9essayer cet examen pratique", 
    "Type into this box to filter down the list of available %s.": "\u00c9crivez dans cette zone pour filtrer la liste des \u00ab\u00a0%s\u00a0\u00bb disponibles.", 
    "Unable to load": "Incapable de charger", 
    "Unexpected server error.": "Erreur de serveur inattendue.", 
    "Ungraded Practice Exam": "Examen de pratique non not\u00e9", 
    "Unit Name": "Nom de l'unit\u00e9", 
    "Units": "Unit\u00e9s", 
    "Unnamed Option": "Option sans nom", 
    "Verified": "V\u00e9rifi\u00e9", 
    "View my exam": "Voir mon examen", 
    "Waiting": "En attente", 
    "Warning": "Attention", 
    "Yesterday": "Hier", 
    "You can also retry this practice exam": "Vous pouvez \u00e9galement r\u00e9essayer cet examen pratique", 
    "You can upload files with these file types: ": "Vous pouvez t\u00e9l\u00e9verser des fichiers avec ces formats : ", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Vous avez ajout\u00e9 un crit\u00e8re. Vous devrez s\u00e9lectionner une option pour le crit\u00e8re dans l'\u00e9tape de formation de l'apprenant. Pour ce faire, cliquez sur l'onglet Param\u00e8tres.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Vous avez supprim\u00e9 un crit\u00e8re. Le crit\u00e8re a \u00e9t\u00e9 retir\u00e9 de l'exemple des r\u00e9ponses dans l'\u00e9tape de formation de l'apprenant.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Vous avez supprim\u00e9 toutes les options pour ce crit\u00e8re. Le crit\u00e8re a \u00e9t\u00e9 retir\u00e9 des exemples de r\u00e9ponses dans l'\u00e9tape de formation de l'apprenant.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Vous avez supprim\u00e9 une option. Cette option a \u00e9t\u00e9 retir\u00e9e de son crit\u00e8re dans les \u00e9chantillons de r\u00e9ponses dans l'\u00e9tape de formation de l'apprenant. Vous pourriez avoir \u00e0 s\u00e9lectionner une nouvelle option pour le crit\u00e8re.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Vous avez s\u00e9lectionn\u00e9 une action, et vous n'avez fait aucune modification sur des champs. Vous cherchez probablement le bouton Envoyer et non le bouton Sauvegarder.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Vous avez s\u00e9lectionn\u00e9 une action, mais vous n'avez pas encore sauvegard\u00e9 certains champs modifi\u00e9s. Cliquez sur OK pour sauver. Vous devrez r\u00e9appliquer l'action.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Vous avez des modifications non sauvegard\u00e9es sur certains champs \u00e9ditables. Si vous lancez une action, ces modifications vont \u00eatre perdues.", 
    "You must provide a learner name.": "Vous devez fournir le nom d'un apprenant.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Vous \u00eates sur le point de soumettre votre r\u00e9ponse pour ce devoir. Apr\u00e8s avoir soumis la r\u00e9ponse, vous ne pouvez pas la modifier ou soumettre une nouvelle r\u00e9ponse.", 
    "Your file ": "Votre fichier", 
    "active proctored exams": "examens surveill\u00e9s actifs", 
    "could not determine the course_id": "impossible de d\u00e9terminer l'id de cours", 
    "courses with active proctored exams": "cours avec des examens surveill\u00e9s actifs", 
    "internally reviewed": "R\u00e9vis\u00e9 en interne", 
    "one letter Friday\u0004F": "V", 
    "one letter Monday\u0004M": "L", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "D", 
    "one letter Thursday\u0004T": "J", 
    "one letter Tuesday\u0004T": "M", 
    "one letter Wednesday\u0004W": "M", 
    "pending": "en attente", 
    "practice": "pratique", 
    "proctored": "surveill\u00e9", 
    "satisfactory": "satisfaisant", 
    "timed": "minut\u00e9", 
    "unsatisfactory": "insatisfaisant", 
    "you have less than a minute remaining": "il vous reste moins d'une minute", 
    "you have {remaining_time} remaining": "il vous reste {remaining_time}", 
    "you will have ": "vous aurez", 
    "your course": "votre cours", 
    "{num_of_hours} hour": "{num_of_hours} heure", 
    "{num_of_hours} hours": "{num_of_hours} heures", 
    "{num_of_minutes} minute": "{num_of_minutes} minutes", 
    "{num_of_minutes} minutes": "{num_of_minutes} minutes"
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
    "DATETIME_FORMAT": "j F Y H:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S", 
      "%d/%m/%Y %H:%M:%S.%f", 
      "%d/%m/%Y %H:%M", 
      "%d/%m/%Y", 
      "%d.%m.%Y %H:%M:%S", 
      "%d.%m.%Y %H:%M:%S.%f", 
      "%d.%m.%Y %H:%M", 
      "%d.%m.%Y", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d"
    ], 
    "DATE_FORMAT": "j F Y", 
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y", 
      "%d/%m/%y", 
      "%d.%m.%Y", 
      "%d.%m.%y", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "j N Y H:i", 
    "SHORT_DATE_FORMAT": "j N Y", 
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

