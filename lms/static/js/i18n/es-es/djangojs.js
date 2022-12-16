

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = (n != 1);
    if (typeof v === 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  const newcatalog = {
    "\n                After the due date has passed, you can review the exam, but you cannot change your answers.\n            ": "\nDespu\u00e9s de que haya pasado la fecha l\u00edmite, puede revisar el examen, pero no puede cambiar sus respuestas.",
    "\n                The time allotted for this exam has expired. Your exam has been submitted and any work you completed\n                will be graded.\n            ": "\nEl tiempo asignado para este examen ha expirado. Su examen ha sido enviado y cualquier trabajo que haya completado ser\u00e1 calificado.",
    "\n                You have submitted your timed exam.\n            ": "\nHa enviado tu examen cronometrado.",
    "\n                Your proctoring session was reviewed successfully. Go to your progress page to view your exam grade.\n            ": "\nSu sesi\u00f3n de supervisi\u00f3n se revis\u00f3 con \u00e9xito. Vaya a su p\u00e1gina de progreso para ver la calificaci\u00f3n de su examen.",
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\nNo cierre esta ventana antes de terminar su examen. si cierra esta ventana, su sesi\u00f3n de supervisi\u00f3n finaliza y no completar\u00e1 con \u00e9xito el examen supervisado.",
    "\n            If you have issues relating to proctoring, you can contact %(provider_name)s technical support by emailing %(provider_tech_support_email)s  or by calling %(provider_tech_support_phone)s.\n          ": "\nSi tiene problemas relacionados con la supervisi\u00f3n, puede comunicarse con el soporte t\u00e9cnico %(provider_name)s enviando un correo electr\u00f3nico %(provider_tech_support_email)s o llamando %(provider_tech_support_phone)s.",
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\nRegrese a la ventana del curso %(platform_name)s para comenzar su examen. Cuando haya terminado su examen y lo haya marcado como completo, puede cerrar esta ventana para finalizar la sesi\u00f3n de supervisi\u00f3n y cargar los datos de la sesi\u00f3n de supervisi\u00f3n para su revisi\u00f3n.",
    "\n          %(platform_name)s Rules for Online Proctored Exams\n      ": "\n%(platform_name)s Reglas para los ex\u00e1menes supervisados en l\u00ednea",
    "\n          Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n        ": "\nCopie este c\u00f3digo de examen \u00fanico. Se le pedir\u00e1 que pegue este c\u00f3digo m\u00e1s tarde antes de comenzar el examen.",
    "\n          For security and exam integrity reasons, we ask you to sign in to your edX account. Then we will direct you to the RPNow proctoring experience.\n        ": "\nPor razones de seguridad e integridad del examen, le pedimos que inicie sesi\u00f3n en su cuenta edX. Luego lo dirigiremos a la experiencia de supervisi\u00f3n de RPNow.",
    "\n          Note: As part of the proctored exam setup, you will be asked\n          to verify your identity. Before you begin, make sure you are\n          on a computer with a webcam, and that you have a valid form\n          of photo identification such as a driver\u2019s license or\n          passport.\n        ": "\n         Nota: Como parte de la configuraci\u00f3n del examen supervisado, se te solicitar\u00e1 \n         verificar tu identidad. Antes de empezar, aseg\u00farate de que cuentas con\n         un ordenador con c\u00e1mara web y de que tienes un documento v\u00e1lido\n          de identificaci\u00f3n con tu foto como el carn\u00e9 de conducir o\n          el pasaporte.\n        ",
    "\n          Step 1\n        ": "\n          Paso 1\n        ",
    "\n          Step 2\n        ": "\nPaso 2",
    "\n          Step 3\n        ": "\nPaso 3",
    "\n          You will be guided through steps to set up online proctoring software and verify your identity.\n        ": "\nSe le guiar\u00e1 a trav\u00e9s de los pasos para configurar el software de supervisi\u00f3n en l\u00ednea y verificar su identidad.",
    "\n         You must adhere to the following rules while you complete this exam.\n         <strong>If you violate these rules, you will receive a score of 0 on the exam, and you will not be eligible for academic course credit.\n         </strong></br>\n      ": "\nDebe cumplir con las siguientes reglas mientras completa este examen. <strong>Si se infringe estas reglas, recibir\u00e1 una calificaci\u00f3n de 0 en el examen y no ser\u00e1 elegible para recibir cr\u00e9dito por cursos acad\u00e9micos.</strong></br>",
    "\n        &#8226; You have %(total_time)s to complete this exam. </br>\n        &#8226; Once you start the exam, you cannot stop the timer. </br>\n        &#8226; For all question types, you must click \"submit\" to complete your answer. </br>\n        &#8226; If time expires before you click \"End My Exam\", only your submitted answers will be graded.\n      ": "\n\u2022 Tiene %(total_time)s para completar este examen.</br> \u2022 Una vez que comience el examen, no podr\u00e1 detener el cron\u00f3metro.</br> \u2022 Para todos los tipos de preguntas, debe hacer clic en &quot;enviar&quot; para completar su respuesta.</br> \u2022 Si se agota el tiempo antes de hacer clic en \"Terminar mi examen\" solo se calificar\u00e1n las respuestas enviadas.",
    "\n        A system error has occurred with your proctored exam. Please reach out to \n        <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">%(platform_name)s Support</a> for \n        assistance, and return to the exam once you receive further instructions.\n      ": "\nSe ha producido un error del sistema con su examen supervisado. Comun\u00edquese con el servicio de <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">asistencia t\u00e9cnica %(platform_name)s</a> para obtener ayuda y regrese al examen una vez que reciba m\u00e1s instrucciones.",
    "\n        A system error has occurred with your proctored exam. Please reach out to your course \n        team at <a href=\"mailto:%(proctoring_escalation_email)s\">%(proctoring_escalation_email)s</a> \n        for assistance, and return to the exam once you receive further instructions.\n      ": "\nSe ha producido un error del sistema con su examen supervisado. Comun\u00edquese con su equipo del curso al <a href=\"mailto:%(proctoring_escalation_email)s\">%(proctoring_escalation_email)s </a> para obtener ayuda y regrese al examen una vez que reciba m\u00e1s instrucciones.",
    "\n        About Proctored Exams\n        ": "\n        Acerca de ex\u00e1menes supervisados\n        ",
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n        \u00bfSeguro que quieres hacer este examen sin supervisi\u00f3n?\n      ",
    "\n        Create your onboarding profile for faster access in the future\n      ": "\nCree su perfil de incorporaci\u00f3n para un acceso m\u00e1s r\u00e1pido en el futuro",
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\n        Debido a que no se han satisfecho algunos prerrequisitos, solo puedes realizar este examen sin supervisi\u00f3n.\n      ",
    "\n        Establish your identity with the proctoring system to take a proctored exam\n      ": "\nEstablezca su identidad con el sistema de supervisi\u00f3n para realizar un examen supervisado",
    "\n        Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n        on your grade in the course.\n      ": "\nFamiliar\u00edcese con la supervisi\u00f3n de ex\u00e1menes reales m\u00e1s adelante en el curso. Este examen de pr\u00e1ctica no tiene impacto en su calificaci\u00f3n en el curso.",
    "\n        Hello %(username)s,\n    ": "\n        Hola, %(username)s:\n    ",
    "\n        I am ready to start this timed exam.\n      ": "\n        Estoy listo para empezar este examen cronometrado.\n      ",
    "\n        If you cannot find this email, you can <a href=\"%(reset_link)s\" target=\"_blank\">reset your password</a> to\n        activate your account.\n      ": "\nSi no puede encontrar este correo electr\u00f3nico, puede <a href=\"%(reset_link)s\" target=\"_blank\">restablecer su contrase\u00f1a</a> para activar su cuenta.",
    "\n        If you cannot find this email, you can reset your password to activate your account.\n      ": "\nSi no puede encontrar este correo electr\u00f3nico, puede restablecer su contrase\u00f1a para activar su cuenta.",
    "\n        If you have concerns about your proctoring session results, contact your course team.\n      ": "\nSi tiene inquietudes sobre los resultados de su sesi\u00f3n de supervisi\u00f3n, comun\u00edquese con el equipo del curso.",
    "\n        If you have questions about the status of your proctoring session results, contact %(platform_name)s Support.\n      ": "\nSi tiene preguntas sobre el estado de los resultados de su sesi\u00f3n de supervisi\u00f3n, comun\u00edquese con Soporte %(platform_name)s.",
    "\n        If you take this exam without proctoring, you will not be eligible for course credit or the MicroMasters credential if either applies to this course.\n      ": "\nSi realiza este examen sin supervisi\u00f3n, no ser\u00e1 elegible para cr\u00e9dito del curso o la credencial de MicroMasters si se aplica a este curso.",
    "\n        Make sure you:\n      ": "\nAseg\u00farese:",
    "\n        No, I want to continue working.\n      ": "\n        No, quiero seguir trabajando.\n      ",
    "\n        No, I'd like to continue working\n      ": "\n        No, prefiero seguir trabajando\n      ",
    "\n        Once your profile has been reviewed, you will receive an email with review results. The email will come from\n        <a href=\"mailto:%(learner_notification_from_email)s\">%(learner_notification_from_email)s</a>.\n        Make sure this email has been added to your inbox filter.\n      ": "\nUna vez que se haya revisado su perfil, recibir\u00e1 un correo electr\u00f3nico con los resultados de la revisi\u00f3n. El correo electr\u00f3nico provendr\u00e1 de <a href=\"mailto:%(learner_notification_from_email)s\">%(learner_notification_from_email)s</a> . Aseg\u00farese de que este correo electr\u00f3nico se haya agregado a su filtro de bandeja de entrada.",
    "\n        Please contact\n        <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a>\n        if you have questions.\n      ": "\nComun\u00edquese con <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> si tiene preguntas.",
    "\n        Practice exams do not affect your grade.\n        You have completed this practice exam and can continue with your course work.\n      ": "\nLos ex\u00e1menes de pr\u00e1ctica no afectan su calificaci\u00f3n. Ha completado este examen de pr\u00e1ctica y puede continuar con su trabajo de curso.",
    "\n        Practice taking a proctored test\n      ": "\nPractique tomando una prueba supervisada",
    "\n        Select the exam code, then copy it using Control + C (Windows) or Command + C (Mac).\n      ": "\nSeleccione el c\u00f3digo del examen, luego c\u00f3pielo usando Control + C (Windows) o Comando + C (Mac).",
    "\n        Start your system check now. A new window will open for this step and you will verify your identity.\n      ": "\nInicie la comprobaci\u00f3n de su sistema ahora. Se abrir\u00e1 una nueva ventana para este paso y verificar\u00e1 su identidad.",
    "\n        The following additional rules apply to this exam. These rules take precedence over the Rules for Online Proctored Exams.</br> </br>\n\n        %(exam_review_policy)s </br>\n      ": "\nLas siguientes reglas adicionales se aplican a este examen. Estas reglas prevalecen sobre las Reglas para los ex\u00e1menes supervisados en l\u00ednea.</br></br> %(exam_review_policy)s</br>",
    "\n        The result will be visible after <strong id=\"wait_deadline\"> Loading... </strong>\n    ": "\nEl resultado ser\u00e1 visible despu\u00e9s de <strong id=\"wait_deadline\">Cargar...</strong>",
    "\n        There was a problem with your practice proctoring session\n      ": "\nHubo un problema con su sesi\u00f3n de supervisi\u00f3n de pr\u00e1ctica",
    "\n        To appeal your proctored exam results, please reach out with any relevant information\n        about your exam at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\nPara apelar los resultados de su examen supervisado, comun\u00edquese con cualquier informaci\u00f3n relevante sobre su examen en <a href=\"%(contact_url)s\">%(contact_url_text)s</a> .",
    "\n        To be eligible for credit or the program credential associated with this course, you must pass the proctoring review for this exam.\n    ": "\nPara ser apto para el cr\u00e9dito o la credencial del programa asociado con este curso, debe aprobar la revisi\u00f3n de supervisi\u00f3n para este examen.",
    "\n        Try a proctored exam\n      ": "\nPrueba un examen supervisado",
    "\n        You have submitted this practice proctored exam\n      ": "\nHa enviado este examen supervisado de pr\u00e1ctica",
    "\n        You will be guided through steps to set up online proctoring software and verify your identity.</br>\n      ": "\nSe le guiar\u00e1 a trav\u00e9s de los pasos para configurar el software de supervisi\u00f3n en l\u00ednea y verificar su identidad.</br>",
    "\n        You will have %(total_time)s to complete your exam.\n    ": "\nTendr\u00e1 %(total_time)s para completar su examen.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and the\n        course team has identified one or more violations of the proctored exam rules. Examples\n        of issues that may result in a rules violation include browsing\n        the internet, blurry or missing photo identification, using a phone,\n        or getting help from another person. As a result of the identified issue(s),\n        you did not successfully meet the proctored exam requirements.\n    ": "\nSu examen supervisado \"%(exam_name)s\" en <a href=\"%(course_url)s\">%(course_name)s</a>\" fue revisado y el equipo del curso identific\u00f3 una o m\u00e1s violaciones de las reglas del examen supervisado. Los ejemplos de problemas que pueden resultar en una violaci\u00f3n de las reglas incluyen navegar por Internet, una identificaci\u00f3n con foto borrosa o faltante, usar un tel\u00e9fono u obtener ayuda de otra persona. Como resultado de los problema(s) identificado, no cumpli\u00f3 satisfactoriamente con los requisitos del examen supervisado.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and you\n        met all proctoring requirements.\n    ": "\nSe revis\u00f3 su examen supervisado \"%(exam_name)s\" en <a href=\"%(course_url)s\">%(course_name)s</a> y cumpli\u00f3 con todos los requisitos de supervisi\u00f3n.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was submitted\n        successfully and will now be reviewed to ensure all exam\n        rules were followed. You should receive an email with your exam\n        status within 5 business days.\n    ": "\nSu examen supervisado \"%(exam_name)s\" en <a href=\"%(course_url)s\">%(course_name)s</a> se envi\u00f3 correctamente y ahora se revisar\u00e1 para garantizar que se hayan seguido todas las reglas del examen. Deber\u00eda recibir un correo electr\u00f3nico con el estado de su examen dentro de los 5 d\u00edas h\u00e1biles.",
    "\n        Your proctoring session ended before you completed this practice exam.\n        You can retry this practice exam if you had problems setting up the online proctoring software.\n      ": "\nSu sesi\u00f3n de supervisi\u00f3n termin\u00f3 antes de que completara este examen de pr\u00e1ctica. Puede volver a intentar este examen de pr\u00e1ctica si tuvo problemas para configurar el software de supervisi\u00f3n en l\u00ednea.",
    "\n        Your proctoring session was reviewed, but did not pass all requirements\n      ": "\nSe revis\u00f3 su sesi\u00f3n de supervisi\u00f3n, pero no pas\u00f3 todos los requisitos",
    "\n      Additional Exam Rules\n    ": "\nReglas de examen adicionales",
    "\n      After you submit your exam, your exam will be graded.\n    ": "\n      Despu\u00e9s de enviar tu examen, \u00e9ste ser\u00e1 evaluado.\n    ",
    "\n      Alternatively, you can end your exam.\n    ": "\nAlternativamente, puede finalizar su examen.",
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n      \u00bfSeguro que quieres enviar tu examen cronometrado?\n    ",
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      \u00bfSeguro que quieres terminar tu examen supervisado?\n    ",
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\n      Dado que la fecha l\u00edmite ha pasado, ya no es posible realizar este examen.\n    ",
    "\n      Error with proctored exam\n    ": "\n      Error con el examen supervisado\n    ",
    "\n      If you already have an onboarding profile approved through another course,\n      this submission will not be reviewed. You may retry this exam at any time\n      to validate that your setup still meets the requirements for proctoring.\n    ": "\nSi ya tiene un perfil de incorporaci\u00f3n aprobado a trav\u00e9s de otro curso, esta presentaci\u00f3n no se revisar\u00e1. Puede volver a intentar este examen en cualquier momento para validar que su configuraci\u00f3n a\u00fan cumple con los requisitos para la supervisi\u00f3n.",
    "\n      If you continue to have trouble please contact <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">\n      %(platform_name)s Support</a>.\n    ": "\nSi sigue teniendo problemas, p\u00f3ngase en contacto con <a href=\"%(link_urls.contact_us)s\" target=\"_blank\">el servicio de asistencia t\u00e9cnica %(platform_name)s</a> .",
    "\n      If you do not have an onboarding profile with the system,\n      Verificient will review your submission and create an onboarding\n      profile to grant you access to proctored exams. Onboarding\n      profile review can take 2+ business days.\n    ": "\nSi no tiene un perfil de ingreso con el sistema, Verificient revisar\u00e1 su env\u00edo y crear\u00e1 un perfil de incorporaci\u00f3n para otorgarle acceso a los ex\u00e1menes supervisados. La revisi\u00f3n del perfil de incorporaci\u00f3n puede demorar m\u00e1s de 2 d\u00edas h\u00e1biles.",
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\nSi tiene discapacidades, puede ser elegible para una asignaci\u00f3n de tiempo adicional en los ex\u00e1menes cronometrados. Solicite a su equipo del curso informaci\u00f3n sobre asignaciones de tiempo adicionales.",
    "\n      If you have made an error in this submission you may restart the onboarding process. \n      Your current submission will be removed and will not receive a review.\n    ": "\nSi ha cometido un error en este env\u00edo, puede reiniciar el proceso de incorporaci\u00f3n. Su presentaci\u00f3n actual ser\u00e1 eliminada y no recibir\u00e1 una revisi\u00f3n.",
    "\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\nSi tiene preguntas sobre el estado de los resultados de su examen supervisado, comun\u00edquese con el soporte %(platform_name)s.",
    "\n      If you have questions about the status of your requirements, contact %(platform_name)s Support.\n    ": "\nSi tiene preguntas sobre el estado de sus requisitos, comun\u00edquese con Soporte %(platform_name)s.",
    "\n      Important\n    ": "\nImportante",
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\nConfirme que haya seleccionado \"Enviar\" para cada problema antes de enviar examen completo.",
    "\n      Once your profile has been reviewed, you will receive an email\n      with review results. The email will come from\n      <a href=\"mailto:%(learner_notification_from_email)s\">\n        %(learner_notification_from_email)s\n      </a>,\n      so make sure this email has been added to your inbox filter.\n    ": "\nUna vez que se haya revisado su perfil, recibir\u00e1 un correo electr\u00f3nico con los resultados de la revisi\u00f3n. El correo electr\u00f3nico provendr\u00e1 de <a href=\"mailto:%(learner_notification_from_email)s\">%(learner_notification_from_email)s</a> , as\u00ed que aseg\u00farese de que este correo electr\u00f3nico se haya agregado a su filtro de bandeja de entrada.",
    "\n      Please check your registered email's Inbox and Spam folders for an activation email from\n      %(platform_name)s.\n    ": "\nVerifique las carpetas de correo no deseado y la bandeja de entrada de su correo electr\u00f3nico registrado para obtener un correo electr\u00f3nico de activaci\u00f3n de %(platform_name)s.",
    "\n      Please complete an onboarding exam before attempting this exam.\n    ": "\nComplete un examen de incorporaci\u00f3n antes de intentar este examen.",
    "\n      Please contact\n      <a href=\"mailto:%(integration_specific_email)s\">\n        %(integration_specific_email)s\n      </a> if you have questions.\n    ": "\nComun\u00edquese con <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> si tiene preguntas.",
    "\n      Please contact\n      <a href=\"mailto:%(integration_specific_email)s\">\n        %(integration_specific_email)s\n      </a> if you have questions. You may retake this onboarding exam by clicking \"Retry my exam\".\n    ": "\nComun\u00edquese con <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> si tiene preguntas. Puede volver a realizar este examen de ingreso haciendo clic en \"Reintentar mi examen\".",
    "\n      Proctored Exam Rules\n    ": "\nReglas de examen supervisado",
    "\n      Proctoring for this course is provided via %(provider_name)s.  Onboarding review, including identity verification, can take 2+ business days.\n    ": "\nLa supervisi\u00f3n de este curso se proporciona a trav\u00e9s de %(provider_name)s. La revisi\u00f3n de incorporaci\u00f3n, incluida la verificaci\u00f3n de identidad, puede demorar m\u00e1s de 2 d\u00edas h\u00e1biles.",
    "\n      Proctoring for your exam is provided via %(provider_name)s.\n      If you have questions about the status of your onboarding exam, contact\n      <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a>.\n    ": "\nLa supervisi\u00f3n de su examen se proporciona a trav\u00e9s de %(provider_name)s. Si tiene preguntas sobre el estado de su examen de incorporaci\u00f3n, comun\u00edquese con <a href=\"mailto:%(integration_specific_email)s\">%(integration_specific_email)s</a> .",
    "\n      Set up and start your proctored exam\n    ": "\nConfigure y comience su examen supervisado",
    "\n      The content of this exam can only be viewed through the RPNow\n      application. If you have yet to complete your exam, please\n      return to the RPNow application to proceed.\n    ": "\nEl contenido de este examen solo se puede ver a trav\u00e9s de la aplicaci\u00f3n RPNow. Si a\u00fan tiene que completar su examen, regrese a la aplicaci\u00f3n RPNow para continuar.",
    "\n      The due date for this exam has passed\n    ": "\nLa fecha l\u00edmite para este examen ha vencido.",
    "\n      This exam is proctored\n    ": "\n      Este examen es supervisado\n    ",
    "\n      To be eligible for credit or the program credential associated with this course, you must pass the proctoring review for this exam.\n\n    ": "\nPara ser apto para el cr\u00e9dito o la credencial del programa asociado con este curso, debe aprobar la revisi\u00f3n de supervisi\u00f3n para este examen.",
    "\n      To view your exam questions and responses, select <strong>View my exam</strong>. The exam's review status is shown in the left navigation pane.\n    ": "\nPara ver las preguntas y respuestas de su examen, seleccione <strong>Ver mi examen</strong> . El estado de revisi\u00f3n del examen se muestra en el panel de navegaci\u00f3n izquierdo.",
    "\n      Why this is important to you:\n    ": "\nPor qu\u00e9 esto es importante para usted:",
    "\n      Yes, submit my timed exam.\n    ": "\n      S\u00ed, enviar mi examen cronometrado.\n    ",
    "\n      You are taking \"%(exam_display_name)s\" as an onboarding exam. You must click \u201cYes, end my proctored exam\u201d and submit your proctoring session to complete onboarding.\n    ": "\nEst\u00e1 realizando \"%(exam_display_name)s\" como examen de ingreso. Debe hacer clic en \"S\u00ed, finalizar mi examen supervisado\" y enviar su sesi\u00f3n de supervisi\u00f3n para completar el ingreso.",
    "\n      You have not activated your account.\n    ": "\nNo ha activado su cuenta.",
    "\n      You have submitted this proctored exam for review\n    ": "\n      Has enviado tu examen supervisado para revisi\u00f3n\n    ",
    "\n      You must complete an onboarding exam before taking this proctored exam\n    ": "\nDebe completar un examen de incorporaci\u00f3n antes de realizar este examen supervisado",
    "\n      Your %(platform_name)s account has not yet been activated. To take the proctored exam,\n      you are required to activate your account.\n    ": "\n      No has activado a\u00fan tu cuenta de  %(platform_name)s. Para realizar el examen supervisado,\n      es necesario que actives tu cuenta primero.\n    ",
    "\n      Your exam is ready to be resumed.\n    ": "\nSu examen est\u00e1 listo para ser reanudado.",
    "\n      Your onboarding exam failed to pass all requirements.\n    ": "\nSu examen de ingreso no pas\u00f3 todos los requisitos.",
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\n      Resultado de tu pr\u00e1ctica supervisada: <b class=\"failure\"> No satisfactoria </b>\n    ",
    "\n      Your profile has been established, and you're ready to take proctored exams in this course.\n    ": "\nSe ha establecido su perfil y est\u00e1 listo para realizar los ex\u00e1menes supervisados de este curso.",
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n%(exam_name)s es un examen cronometrado (%(total_time)s)",
    "\n    Error: There was a problem with your onboarding session\n  ": "\nError: Ocurri\u00f3 un problema con su sesi\u00f3n de incorporaci\u00f3n",
    "\n    If you have any questions about your results, you can reach out at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\nSi tiene alguna pregunta sobre sus resultados, puede comunicarse con <a href=\"%(contact_url)s\">%(contact_url_text)s</a> .",
    "\n    Proctoring onboarding exam\n  ": "\nSupervisi\u00f3n del examen de ingreso",
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\n    Los siguientes requisitos est\u00e1n <strong>pendientes</strong> y deben ser complidos con \u00e9xito antes de que puedas proceder:\n    ",
    "\n    You can take this exam with proctoring only when all prerequisites have been successfully completed.\n    ": "\nPuede realizar este examen con supervisi\u00f3n solo cuando se hayan completado con \u00e9xito todos los requisitos previos.",
    "\n    You did not satisfy the following prerequisites:\n    ": "\n    No se han satisfecho los siguientes prerrequisitos:\n    ",
    "\n    You did not satisfy the requirements for taking this exam with proctoring.\n    ": "\nNo cumpli\u00f3 con los requisitos para realizar este examen con supervisi\u00f3n.",
    "\n    You have not completed the prerequisites for this exam. All requirements must be satisfied before you can take this proctored exam.\n    ": "\nNo ha completado los requisitos previos para este examen. Se deben cumplir todos los requisitos antes de poder realizar este examen supervisado.",
    "\n    You have submitted this onboarding exam\n  ": "\nEnvi\u00f3 este examen de ingreso",
    "\n    You will be guided through online proctoring software set up and identity verification.\n  ": "\nSe lo guiar\u00e1 a trav\u00e9s de la configuraci\u00f3n del software de supervisi\u00f3n en l\u00ednea y la verificaci\u00f3n de identidad.",
    "\n    Your onboarding exam is being reviewed. Before attempting this exam, please allow 2+ business days for your onboarding exam to be reviewed.\n  ": "\nSu examen de ingreso est\u00e1 siendo revisado. Antes de intentar este examen, espere m\u00e1s de 2 d\u00edas h\u00e1biles para que se revise su examen de ingreso.",
    "\n    Your onboarding profile was reviewed successfully\n  ": "\nSu perfil de ingreso se revis\u00f3 con \u00e9xito",
    "\n    Your onboarding session was reviewed, but did not pass all requirements\n  ": "\nSe revis\u00f3 su sesi\u00f3n de ingreso, pero no pas\u00f3 todos los requisitos",
    "\n    Your proctoring session ended before you completed this onboarding exam.\n    You should retry this onboarding exam.\n  ": "\nSu sesi\u00f3n de supervisi\u00f3n finaliz\u00f3 antes de completar este examen de ingreso. Debe volver a intentar este examen de ingreso.",
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": "A partir de este momento, debe seguir las <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">reglas de supervisi\u00f3n en l\u00ednea</a> para aprobar la revisi\u00f3n de supervisi\u00f3n de su examen.",
    " Your Proctoring Session Has Started ": "Tu sesi\u00f3n de supervisi\u00f3n ha comenzado",
    " and {num_of_minutes} minute": " y {num_of_minutes} minuto",
    " and {num_of_minutes} minutes": " y {num_of_minutes} minutos",
    " to complete and submit the exam.": "para completar y enviar el examen.",
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s seleccionado",
      "%(sel)s de  %(cnt)s seleccionados"
    ],
    "(required):": "(obligatorio):",
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "Additional Time (minutes)": "Tiempo adicional (minutes)",
    "After you select ": "Despu\u00e9s de seleccionar",
    "All Unreviewed": "Todo sin revisar",
    "All Unreviewed Failures": "Todas las fallas no revisadas",
    "April": "Abril",
    "Are you sure you want to delete the following file? It cannot be restored.\nFile: ": "\u00bfSeguro que quieres eliminar el siguiente archivo? No se podr\u00e1 restaurar.\nArchivo:",
    "Assessment": "Tarea",
    "Assessments": "Tareas",
    "August": "Agosto",
    "Available %s": "%s Disponibles",
    "Back to Full List": "Volver a la lista completa",
    "Block view is unavailable": "La vista en bloque no est\u00e1 disponible",
    "Can I request additional time to complete my exam?": "\u00bfPuedo solicitar un tiempo adicional para completar mi examen?",
    "Cancel": "Cancelar",
    "Cannot update attempt review status": "No se puede actualizar el estado de revisi\u00f3n del intento",
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Los cambios en los pasos que no est\u00e1n seleccionados como parte de la tarea no se guardar\u00e1n.",
    "Choose": "Elegir",
    "Choose a Date": "Elija una Fecha",
    "Choose a Time": "Elija una Hora",
    "Choose a time": "Elija una hora",
    "Choose all": "Selecciona todos",
    "Chosen %s": "%s elegidos",
    "Click to choose all %s at once.": "Haga clic para seleccionar todos los %s de una vez",
    "Click to remove all chosen %s at once.": "Haz clic para eliminar todos los %s elegidos",
    "Close": "Cerrar",
    "Confirm": "Confirmar",
    "Confirm Delete Uploaded File": "Confirmar la eliminaci\u00f3n del archivo cargado",
    "Confirm Grade Team Submission": "Confirmar el env\u00edo de la calificaci\u00f3n de equipo",
    "Confirm Submit Response": "Confirmar el env\u00edo de la respuesta",
    "Continue Exam Without Proctoring": "Continuar el examen sin supervisi\u00f3n",
    "Continue to my practice exam": "Continuar con mi examen de pr\u00e1ctica",
    "Continue to my proctored exam.": "Continuar con mi examen supervisado.",
    "Continue to onboarding": "Continuar con el ingreso",
    "Copy Exam Code": "Copiar c\u00f3digo de examen",
    "Could not load teams information.": "No ha podido cargarse la informaci\u00f3n de los equipos.",
    "Could not retrieve download url.": "No se ha podido obtener la URL de descarga.",
    "Could not retrieve upload url.": "No se ha podido obtener la URL de carga.",
    "Course Id": "Identificaci\u00f3n del curso",
    "Created": "Creado",
    "Criterion Added": "Criterio a\u00f1adido",
    "Criterion Deleted": "Criterio eliminado",
    "December": "Diciembre",
    "Declined": "Rechazado",
    "Demo the new Grading Experience": "Demostraci\u00f3n de la nueva Experiencia de Calificaci\u00f3n",
    "Describe ": "Describir",
    "Download Software Clicked": "Software de descarga hecho clic",
    "End My Exam": "Finalizar mi examen",
    "Ending Exam": "Examen final",
    "Enter a valid positive value number": "Introduzca un n\u00famero de valor positivo v\u00e1lido",
    "Enter a valid username or email": "Escribe un nombre de usuario o un correo electr\u00f3nico v\u00e1lido",
    "Error": "Error",
    "Error getting the number of ungraded responses": "Error al obtener el n\u00famero de respuestas sin calificar",
    "Error when looking up username": "Error al buscar el nombre de usuario",
    "Error while fetching student data.": "Error al obtener los datos de los estudiantes.",
    "Errors detected on the following tabs: ": "Errores detectados en las siguientes pesta\u00f1as:",
    "Failed Proctoring": "Prueba fallida",
    "Failed to clone rubric": "No se ha podido clonar la r\u00fabrica",
    "February": "Febrero",
    "Feedback available for selection.": "Retroalimentaci\u00f3n disponible para tu selecci\u00f3n.",
    "File types can not be empty.": "Los tipos de archivo no pueden estar en blanco",
    "File upload failed: unsupported file type. Only the supported file types can be uploaded. If you have questions, please reach out to the course team.": "Error al cargar el archivo: tipo de archivo no admitido. Solo se pueden cargar los tipos de archivos admitidos. Si tienes alguna pregunta, contacta con el equipo del curso.",
    "Filter": "Filtro",
    "Final Grade Received": "Nota final recibida",
    "Go Back": "Volver atr\u00e1s",
    "Grade Status": "Estado de la calificaci\u00f3n",
    "Have a computer with a functioning webcam": "Tener una computadora con una c\u00e1mara web que funcione",
    "Have your valid photo ID (e.g. driver's license or passport) ready": "Tenga lista su identificaci\u00f3n con foto v\u00e1lida (por ejemplo, licencia de conducir o pasaporte)",
    "Heading 3": "Encabezado 3",
    "Heading 4": "Encabezado 4",
    "Heading 5": "Encabezado 5",
    "Heading 6": "Encabezado 6",
    "Hide": "Ocultar",
    "However, {overwritten_count} of these students have received a grade through the staff grade override tool already.": "Sin embargo, {overwritten_count} de estos estudiantes ya han recibido una calificaci\u00f3n a trav\u00e9s de la herramienta de sobrescritura de calificaci\u00f3n por el equipo docente.",
    "I am ready to start this timed exam,": "Estoy listo para comenzar este examen cronometrado,",
    "I understand and want to reset this onboarding exam.": "Entiendo y quiero restablecer este examen de incorporaci\u00f3n.",
    "If the proctoring software window is still open, close it now and confirm that you want to quit the application.": "Si la ventana del software de supervisi\u00f3n a\u00fan est\u00e1 abierta, ci\u00e9rrela ahora y confirme que desea salir de la aplicaci\u00f3n.",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Si abandonas esta p\u00e1gina sin guardar o enviar tu respuesta, perder\u00e1s todo el trabajo que hayas realizado en la respuesta.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Si abandonas esta p\u00e1gina sin enviar tu evaluaci\u00f3n por pares, perder\u00e1s todo el trabajo que hayas realizado.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Si abandonas esta p\u00e1gina sin enviar tu autoevaluaci\u00f3n, perder\u00e1s todo el trabajo que hayas realizado.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Si abandonas esta p\u00e1gina sin enviar tu evaluaci\u00f3n, perder\u00e1s todo el trabajo que hayas realizado.",
    "Individual file size must be {max_files_mb}MB or less.": "Cada archivo individual debe tener {max_files_mb}MB como m\u00e1ximo.",
    "Is Resumable": "es reanudable",
    "Is Sample Attempt": "Intento de prueba",
    "January": "Enero",
    "July": "Julio",
    "June": "Junio",
    "List of Open Assessments is unavailable": "El listado de tareas abiertas no est\u00e1 disponible",
    "Make sure that you have selected \"Submit\" for each answer before you submit your exam.": "Aseg\u00farese de haber seleccionado \"Enviar\" para cada respuesta antes de enviar su examen.",
    "March": "Marzo",
    "May": "Mayo",
    "Midnight": "Medianoche",
    "Missing required query parameter course_id": "Falta el par\u00e1metro obligatorio course_id",
    "Multiple teams returned for course": "Varios equipos han regresado por curso",
    "Must be a Staff User to Perform this request.": "Debes ser un miembro del equipo para realizar esta petici\u00f3n.",
    "Navigate to onboarding exam": "Navegar al examen de incorporaci\u00f3n",
    "No exams in course {course_id}.": "No hay ex\u00e1menes en curso {course_id}.",
    "No instructor dashboard for {proctor_service}": "No hay panel de instructor para {proctor_service}",
    "No onboarding status API for {proctor_service}": "Sin API de estado de ingreso para {proctor_service}",
    "No proctored exams in course {course_id}": "No hay ex\u00e1menes supervisados en curso {course_id}",
    "Noon": "Mediod\u00eda",
    "Not Selected": "No seleccionado",
    "Note: You are %s hour ahead of server time.": [
      "Nota: Usted esta a %s horas por delante de la hora del servidor.",
      "Nota: Usted va %s horas por delante de la hora del servidor."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: Usted esta a %s hora de retraso de tiempo de servidor.",
      "Nota: Usted va %s horas por detr\u00e1s de la hora del servidor."
    ],
    "November": "Noviembre",
    "Now": "Ahora",
    "October": "Octubre",
    "Onboarding Expired": "Incorporaci\u00f3n caducada",
    "Onboarding Failed": "Error de incorporaci\u00f3n",
    "Onboarding Missing": "Falta incorporaci\u00f3n",
    "Onboarding Pending": "Incorporaci\u00f3n pendiente",
    "Onboarding status question": "Pregunta sobre el estado de incorporaci\u00f3n",
    "Once you click \"Yes, end my proctored exam\", the exam will be closed, and your proctoring session will be submitted for review.": "Una vez que haga clic en \"S\u00ed, finalizar mi examen supervisado\", el examen se cerrar\u00e1 y su sesi\u00f3n de supervisi\u00f3n se enviar\u00e1 para su revisi\u00f3n.",
    "One or more rescheduling tasks failed.": "Error en una o m\u00e1s tareas de reprogramaci\u00f3n.",
    "Option Deleted": "Opci\u00f3n eliminada",
    "Paragraph": "P\u00e1rrafo",
    "Passed Proctoring": "Pr\u00e1ctica supervisada",
    "Peer": "Compa\u00f1ero",
    "Peer Responses Received": "Respuestas de compa\u00f1eros recibidas",
    "Peers Assessed": "Compa\u00f1ero evaluado",
    "Pending Session Review": "Revisi\u00f3n de la sesi\u00f3n pendiente",
    "Please wait": "Por favor, espera",
    "Practice Exam Completed": "Examen pr\u00e1ctico completado",
    "Practice Exam Failed": "Examen pr\u00e1ctico fallido",
    "Preformatted": "Preformateado",
    "Problem cloning rubric": "Problema al duplicar la r\u00fabrica",
    "Proctored Option Available": "Opci\u00f3n supervisada disponible",
    "Proctored Option No Longer Available": "Opci\u00f3n supervisada no disponible",
    "Proctored exam {exam_name} in {course_name} for user {username}": "Examen supervisado {exam_name} en {course_name} para {username}",
    "Proctoring Results For {course_name} {exam_name}": "Resultados de supervisi\u00f3n para {course_name} {exam_name}",
    "Proctoring Review In Progress For {course_name} {exam_name}": "Revisi\u00f3n de supervisi\u00f3n en curso para {course_name} {exam_name}",
    "Proctoring results are usually available within 5 business days after you submit your exam.": "Los resultados de supervisi\u00f3n generalmente est\u00e1n disponibles dentro de los 5 d\u00edas h\u00e1biles posteriores a la presentaci\u00f3n del examen.",
    "Ready To Start": "Listo para empezar",
    "Ready To Submit": "Listo para enviar",
    "Ready to Resume": "Listo para reanudar",
    "Refresh": "Refrescar",
    "Rejected": "Rechazado",
    "Remove": "Eliminar",
    "Remove all": "Eliminar todos",
    "Resetting Onboarding Exam": "Restablecimiento del examen de ingreso",
    "Resumed": "reanudado",
    "Retry my exam": "Reintentar mi examen",
    "Review Policy Exception": "Excepci\u00f3n de la pol\u00edtica de revisi\u00f3n",
    "Save Unsuccessful": "Guardado sin \u00e9xito",
    "Saving...": "Guardando...",
    "Second Review Required": "Es necesario revisarlo una segunda vez",
    "Self": "Auto",
    "September": "Septiembre",
    "Server error.": "Error del servidor.",
    "Show": "Mostrar",
    "Staff": "Equipo docente",
    "Staff Grader": "Calificador de personal",
    "Staff assessment": "Evaluaci\u00f3n del equipo docente",
    "Start Exam": "Iniciar examen",
    "Start System Check": "Comenzar comprobaci\u00f3n del sistema",
    "Start my exam": "comenzar mi examen",
    "Started": "Inici\u00f3",
    "Starting Exam": "examen inicial",
    "Status of Your Response": "Estado de tu respuesta",
    "Submitted": "Enviado",
    "Take this exam without proctoring.": "Realizar este examen sin supervisi\u00f3n.",
    "Taking As Open Exam": "Haciendo como examen abierto",
    "Taking As Proctored Exam": "Haciendo como examen supervisado",
    "Taking as Proctored": "Tomando como examen supervisado",
    "The \"{name}\" problem is configured to require a minimum of {min_grades} peer grades, and asks to review {min_graded} peers.": "El problema \"{name}\" est\u00e1 configurado con un m\u00ednimo de {min_grades} calificaciones de compa\u00f1eros y solicita revisar al menos a {min_graded} compa\u00f1eros.",
    "The display of ungraded and checked out responses could not be loaded.": "No se ha podido cargar la visualizaci\u00f3n de respuestas sin calificar y revisadas.",
    "The following file types are not allowed: ": "No se permiten los siguientes tipos de archivos:",
    "The maximum number files that can be saved is ": "El n\u00famero m\u00e1ximo de archivos que se pueden guardar es",
    "The onboarding service is temporarily unavailable. Please try again later.": "El servicio de ingreso no est\u00e1 disponible temporalmente. Por favor, int\u00e9ntelo de nuevo m\u00e1s tarde.",
    "The server could not be contacted.": "No se ha podido contactar con el servidor.",
    "The staff assessment form could not be loaded.": "La evaluaci\u00f3n por el equipo docente no ha podido cargarse.",
    "The submission could not be removed from the grading pool.": "La entrega no ha podido eliminarse del tabl\u00f3n de calificaciones.",
    "There are currently {stuck_learners} learners in the waiting state, meaning they have not yet met all requirements for Peer Assessment. ": "Actualmente se encuentran {stuck_learners} estudiantes en estado de espera, lo cual significa que a\u00fan no cumplen con todos los requisitos para la evaluaci\u00f3n por pares.",
    "There is no onboarding exam accessible to this user.": "No hay ning\u00fan examen de ingreso accesible para este usuario.",
    "There is no onboarding exam related to this course id.": "No hay un examen de ingreso relacionado con esta identificaci\u00f3n de curso.",
    "This ORA has already been released. Changes will only affect learners making new submissions. Existing submissions will not be modified by this change.": "Esta tarea de respuesta abierta ya ha sido publicada. Los cambios solo afectar\u00e1n a los estudiantes que hagan nuevas entregas. Las entregas ya realizadas no se ver\u00e1n modificadas por este cambio.",
    "This assessment could not be submitted.": "Esta tarea no ha podido enviarse.",
    "This exam has a time limit associated with it.": "Este examen tiene un l\u00edmite de tiempo",
    "This feedback could not be submitted.": "La retroalimentaci\u00f3n no ha podido enviarse.",
    "This grade will be applied to all members of the team. Do you want to continue?": "Esta calificaci\u00f3n se aplicar\u00e1 a todos los miembros del equipo. \u00bfQuieres continuar?",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta es la lista de %s disponibles. Puede elegir algunos seleccion\u00e1ndolos en la caja inferior y luego haciendo clic en la flecha \"Elegir\" que hay entre las dos cajas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta es la lista de los %s elegidos. Puede elmininar algunos seleccion\u00e1ndolos en la caja inferior y luego haciendo click en la flecha \"Eliminar\" que hay entre las dos cajas.",
    "This problem could not be saved.": "Este ejercicio no ha podido guardarse.",
    "This response could not be saved.": "Esta respuesta no ha podido guardarse.",
    "This response could not be submitted.": "Esta respuesta no ha podido enviarse.",
    "This response has been saved but not submitted.": "Esta respuesta se ha guardado pero no se ha enviado.",
    "This response has not been saved.": "Esta respuesta no se ha guardado.",
    "This section could not be loaded.": "Esta secci\u00f3n no ha podido cargarse.",
    "Thumbnail view of ": "Vista en miniatura de",
    "Time Spent On Current Step": "Tiempo empleado en el paso actual",
    "Timed Exam": "Examen con Tiempo",
    "Timed Out": "Caducado",
    "To pass this exam, you must complete the problems in the time allowed.": "Para aprobar este examen, debe terminar los ejercicios en el tiempo acordado",
    "Today": "Hoy",
    "Tomorrow": "Ma\u00f1ana",
    "Total Responses": "Respuestas totales",
    "Training": "Pr\u00e1ctica",
    "Type into this box to filter down the list of available %s.": "Escriba en este cuadro para filtrar la lista de %s disponibles",
    "Unable to load": "No se ha podido cargar",
    "Unexpected server error.": "Error inesperado del servidor",
    "Ungraded Practice Exam": "Examen de pr\u00e1ctica no graduado",
    "Unit Name": "Nombre de la unidad",
    "Units": "Unidades",
    "Unnamed Option": "Opci\u00f3n sin nombre",
    "User lookup failed": "Error de b\u00fasqueda de usuario",
    "Username": "Nombre de usuario",
    "Verified": "Verificado",
    "View and grade responses": "Ver y calificar respuestas",
    "View my exam": "Ver mi examen",
    "Waiting": "Esperando",
    "Warning": "Aviso",
    "Yes, end my proctored exam": "S\u00ed, finalizar mi examen supervisado",
    "Yesterday": "Ayer",
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Assessment Steps tab.": "Has agregado un criterio. Deber\u00e1s seleccionar una opci\u00f3n para el criterio en el paso para el entrenamiento del estudiante. Para hacer esto, haz clic en la pesta\u00f1a Pasos de evaluaci\u00f3n.",
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Has eliminado un criterio. El criterio se ha eliminado de las respuestas de ejemplo del paso para el entrenamiento del estudiante.",
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Has eliminado todas las opciones para este criterio. El criterio se ha eliminado de las respuestas de ejemplo del paso para el entrenamiento del estudiante.",
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Has eliminado una opci\u00f3n. Esa opci\u00f3n se ha eliminado de su criterio en las respuestas de ejemplo del paso para el entrenamiento del estudiante. Es posible que tengas que seleccionar una nueva opci\u00f3n para el criterio.",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Ha seleccionado una acci\u00f3n y no ha realizado ning\u00fan cambio en campos individuales. Probablemente est\u00e9 buscando el bot\u00f3n 'Ir' en lugar del bot\u00f3n 'Guardar'.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Ha seleccionado una acci\u00f3n, pero a\u00fan no ha guardado los cambios en los campos individuales. Haga clic en Aceptar para guardar. Deber\u00e1 volver a ejecutar la acci\u00f3n.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tiene cambios sin guardar en campos editables individuales. Si ejecuta una acci\u00f3n, los cambios no guardados se perder\u00e1n.",
    "You must provide a learner name.": "Debes proporcionar el nombre de un estudiante.",
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Est\u00e1s a punto de enviar tu respuesta para esta tarea. Despu\u00e9s de enviar esta respuesta, no podr\u00e1s cambiarla o enviar una nueva.",
    "Your file has been deleted or path has been changed: ": "Su archivo ha sido eliminado o la ruta ha sido cambiada:",
    "Your recorded data should now be uploaded for review.": "Sus datos registrados ahora deben cargarse para su revisi\u00f3n.",
    "a practice exam": "un examen de practica",
    "a proctored exam": "un examen supervisado",
    "a timed exam": "un examen cronometrado",
    "abbrev. month April\u0004Apr": "Abr",
    "abbrev. month August\u0004Aug": "Ago",
    "abbrev. month December\u0004Dec": "Dic",
    "abbrev. month February\u0004Feb": "Feb",
    "abbrev. month January\u0004Jan": "Ene",
    "abbrev. month July\u0004Jul": "Jul",
    "abbrev. month June\u0004Jun": "Jun",
    "abbrev. month March\u0004Mar": "Mar",
    "abbrev. month May\u0004May": "May",
    "abbrev. month November\u0004Nov": "Nov",
    "abbrev. month October\u0004Oct": "Oct",
    "abbrev. month September\u0004Sep": "Sep",
    "active proctored exams": "Ex\u00e1menes supervisados activos",
    "allowance_value": "allowance_value",
    "an onboarding exam": "un examen de incorporaci\u00f3n",
    "could not determine the course_id": "no se pudo determinar el id_del_curso",
    "courses with active proctored exams": "cursos con ex\u00e1menes supervisados activos",
    "error count: ": "recuento de errores:",
    "internally reviewed": "revisado internamente",
    "one letter Friday\u0004F": "V",
    "one letter Monday\u0004M": "L",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "J",
    "one letter Tuesday\u0004T": "M",
    "one letter Wednesday\u0004W": "M",
    "user_info": "user_info",
    "you have less than a minute remaining": "te queda menos de un minuto",
    "you have {remaining_time} remaining": "te queda {remaining_time} restante",
    "you will have ": "Tendr\u00e1",
    "your course": "Tu curso",
    "{num_of_hours} hour": "{num_of_hours} hora",
    "{num_of_hours} hours": "{num_of_hours} horas",
    "{num_of_minutes} minute": "{num_of_minutes} minuto",
    "{num_of_minutes} minutes": "{num_of_minutes} minutos"
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
    "DATETIME_FORMAT": "j \\d\\e F \\d\\e Y \\a \\l\\a\\s H:i",
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
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j \\d\\e F",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d/m/Y H:i",
    "SHORT_DATE_FORMAT": "d/m/Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "H:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F \\d\\e Y"
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

