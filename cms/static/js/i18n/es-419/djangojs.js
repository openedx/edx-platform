

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
    "\n\nThis email is to let you know that the status of your proctoring session review for %(exam_name)s in\n<a href=\"%(course_url)s\">%(course_name)s </a> is %(status)s. If you have any questions about proctoring,\ncontact %(platform)s support at %(contact_email)s.\n\n": "\n\nEste mensaje es para avisarle que el estado de revisi\u00f3n de su examen supervisado para  %(exam_name)s en\n<a href=\"%(course_url)s\">%(course_name)s </a> es %(status)s. Si tiene preguntas sobre la supervisi\u00f3n,\ncomun\u00edquese con el equipo de ayuda para %(platform)s en %(contact_email)s.\n\n", 
    "\n                    Make sure you are on a computer with a webcam, and that you have valid photo identification\n                    such as a driver's license or passport, before you continue.\n                ": "\nAseg\u00farese de que est\u00e9 usando una computadora con c\u00e1mara web, y que tiene una identificaci\u00f3n fotogr\u00e1fica v\u00e1lida\ncomo una licencia para conducir o un pasaporte, antes de seguir.", 
    "\n                    Your verification attempt failed. Please read our guidelines to make\n                    sure you understand the requirements for successfully completing verification,\n                    then try again.\n                ": "\nSu verificaci\u00f3n no fue aprobada. Por favor, lea nuestra gu\u00eda para asegurarse\nde que entienda los requisitos para completar la verificaci\u00f3n exit\u00f3samente,\ny despu\u00e9s intente de nuevo.", 
    "\n                    Your verification has expired. You must successfully complete a new identity verification\n                    before you can start the proctored exam.\n                ": "\nSu verificaci\u00f3n ha expirado. Debe completar la verificaci\u00f3n de identidad nuevamente\nantes de poder iniciar el examen supervisado.", 
    "\n                    Your verification is pending. Results should be available 2-3 days after you\n                    submit your verification.\n                ": "\nSu verificaci\u00f3n est\u00e1 en proceso. Los resultados deben estar disponibles entre 2-3 d\u00edas despu\u00e9s del\nenv\u00edo de su verificaci\u00f3n.", 
    "\n                Complete your verification before starting the proctored exam.\n            ": "\nComplete su verificaci\u00f3n antes de iniciar el examen supervisado.", 
    "\n                You must successfully complete identity verification before you can start the proctored exam.\n            ": "\nEs necesario completar la verificaci\u00f3n de su identidad antes de iniciar el examen supervisado.", 
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\nNo cierre esta ventana antes de completar su examen. Si la cierra, su sesi\u00f3n supervisada terminar\u00e1, y no completar\u00e1 el examen supervisado.", 
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\nRegrese a la ventana del curso de %(platform_name)s para iniciar su examen. Una vez que haya completado su examen y\nlo haya marcado como completo, puede cerrar esta ventana para terminar la sesi\u00f3n supervisada\ny enviar su grabaci\u00f3n para la revisi\u00f3n de los supervisores.", 
    "\n          3. When you have finished setting up proctoring, start the exam.\n        ": "\n3. Una vez que haya terminado de configurar la supervisi\u00f3n, inicie el examen.", 
    "\n          Start my exam\n        ": "\nIniciar mi examen", 
    "\n        &#8226; When you start your exam you will have %(total_time)s to complete it. </br>\n        &#8226; You cannot stop the timer once you start. </br>\n        &#8226; If time expires before you finish your exam, your completed answers will be\n                submitted for review. </br>\n      ": "\n&#8226; Una vez que haya iniciado su examen tendr\u00e1 %(total_time)s para completarlo. </br>\n&#8226; No se puede parar el cronometro una vez iniciado. </br>\n&#8226; Si el tiempo se agota antes de que termine su examen, sus respuestas completadas ser\u00e1n\nenviadas para calificaci\u00f3n. </br>", 
    "\n        1. Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n      ": "\n1. Copie este c\u00f3digo \u00fanico de examen. Se le pedira introducir este c\u00f3digo m\u00e1s tarde antes de iniciar el examen.", 
    "\n        2. Follow the link below to set up proctoring.\n      ": "\n2. Siga en enlace de abajo para configurar la supervisi\u00f3n", 
    "\n        A new window will open. You will run a system check before downloading the proctoring application.\n      ": "\nAparecer\u00e1 una nueva ventana. Usted iniciar\u00e1 una revisi\u00f3n del sistema antes de descargar la aplicaci\u00f3n de supervisi\u00f3n.", 
    "\n        About Proctored Exams\n        ": "\nAcerca de los ex\u00e1menes supervisados", 
    "\n        After the due date has passed, you can review the exam, but you cannot change your answers.\n      ": "\nDespu\u00e9s de que la fecha l\u00edmite ha pasado, podr\u00e1 revisar el examen, pero no podr\u00e1 cambiar sus respuestas.", 
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n\u00bfEst\u00e1 seguro que quiere tomar este examen sin supervisi\u00f3n?", 
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\nDebido a prerrequisitos no cumplidos, solo puede tomar este examen sin supervisi\u00f3n.", 
    "\n        I am not interested in academic credit.\n      ": "\nNo tengo inter\u00e9s en cr\u00e9dito acad\u00e9mico.", 
    "\n        I am ready to start this timed exam.\n      ": "\nEstoy listo/a para empezar este examen cronometrado.", 
    "\n        If you take this exam without proctoring, you will <strong> no longer be eligible for academic credit. </strong>\n      ": "\nSi toma este examen sin supervisi\u00f3n, <strong> ya no ser\u00e1 elegible para cr\u00e9dito acad\u00e9mico. </strong>", 
    "\n        No, I want to continue working.\n      ": "\nNo, quiero seguir trabajando.", 
    "\n        No, I'd like to continue working\n      ": "\nNo, quiero seguir trabajando.", 
    "\n        Select the exam code, then copy it using Command+C (Mac) or Control+C (Windows).\n      ": "\nSeleccione el c\u00f3digo del examen, y c\u00f3pielo usando Command+C (Mac) o Control+C (Windows).", 
    "\n        The time allotted for this exam has expired. Your exam has been submitted and any work you completed will be graded.\n      ": "\nEl tiempo permitido para este examen ha vencido. Su examen ha sido enviado y el progreso que complet\u00f3 ser\u00e1 calificado.", 
    "\n        You have submitted your timed exam.\n      ": "\nHa enviado su examen cronometrado.", 
    "\n        You will be asked to verify your identity as part of the proctoring exam set up.\n        Make sure you are on a computer with a webcam, and that you have valid photo identification\n        such as a driver's license or passport, before you continue.\n      ": "\nLe ser\u00e1 pedido verificar su identidad como parte de la preparaci\u00f3n para el examen supervisado.\nConfirme que est\u00e9 usando una computadora con una c\u00e1mara web, y que tenga una identificaci\u00f3n fotogr\u00e1fica v\u00e1lida\ncomo una licencia para conducir o un pasaporte, antes de seguir.", 
    "\n      &#8226; After you quit the proctoring session, the recorded data is uploaded for review. </br>\n      &#8226; Proctoring results are usually available within 5 business days after you submit your exam.\n    ": "\n&#8226; Despu\u00e9s de salir de la sesi\u00f3n supervisada, los datos grabados son subidos para revisi\u00f3n. </br>\n&#8226; Los resultados de la sesi\u00f3n supervisada normalmente est\u00e1n disponibles dentro de 5 d\u00edas h\u00e1biles despu\u00e9s de el env\u00edo de su examen.", 
    "\n      A technical error has occurred with your proctored exam. To resolve this problem, contact\n      <a href=\"mailto:%(tech_support_email)s\">technical support</a>. All exam data, including answers\n      for completed problems, has been lost. When the problem is resolved you will need to restart\n      the exam and complete all problems again.\n    ": "\nSe\u00a0ha producido un error t\u00e9cnico en su examen supervisado. Para resolver el problema, comun\u00edquese con <a href=\"mailto:%(tech_support_email)s\">ayuda t\u00e9cnica</a>. Todos los datos del examen, incluso respuestas\npara problemas completados, han sido perdidos. Cuando el problema est\u00e9 resuelto, tendr\u00e1 que reiniciar\nel examen y completar todos los problemas de nuevo.", 
    "\n      After the due date for this exam has passed, you will be able to review your answers on this page.\n    ": "\nDespu\u00e9s de que la fecha l\u00edmite de este examen haya pasado, podr\u00e1 revisar sus respuestas en esta p\u00e1gina.", 
    "\n      After you submit your exam, your exam will be graded.\n    ": "\nDespu\u00e9s de enviar el examen, el examen ser\u00e1 calificado.", 
    "\n      After you submit your exam, your responses are graded and your proctoring session is reviewed.\n      You might be eligible to earn academic credit for this course if you complete all required exams\n      as well as achieve a final grade that meets credit requirements for the course.\n    ": "\nDespu\u00e9s de enviar su examen, sus respuestas son calificadas y su sesi\u00f3n supervisada es revisada.\nEs posible que Usted sea elegible para obtener cr\u00e9dito acad\u00e9mico para este curso si cumple con todos los ex\u00e1menes requeridos\nadem\u00e1s de lograr una calificaci\u00f3n final que cumple con los requisitos de cr\u00e9dito para el curso.", 
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n\u00bfEst\u00e1 seguro de que quiere enviar su examen cronometrado?", 
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n\u00bfEst\u00e1 seguro de que quiere terminar su examen supervisado?", 
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\nDebido a que la fecha l\u00edmite ha pasado, ya no puede tomar este examen.", 
    "\n      Error with proctored exam\n    ": "\nError en examen supervisado", 
    "\n      Follow these instructions\n    ": "\nSiga estas instrucciones", 
    "\n      Follow these steps to set up and start your proctored exam.\n    ": "\nSiga estos pasos para preparar e iniciar su examen supervisado.", 
    "\n      Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n      on your grade in the course.\n    ": "\nFamiliaricese con la supervisi\u00f3n para los ex\u00e1menes reales que estar\u00e1n m\u00e1s adelante en el curso. Este examen de pr\u00e1ctica no tiene impacto ninguno\nen su calificaci\u00f3n para el curso.", 
    "\n      If the proctoring software window is still open, you can close it now. Confirm that you want to quit the application when you are prompted.\n    ": "\nSi la aplicaci\u00f3n de supervisi\u00f3n todav\u00eda est\u00e1 abierta, la puede cerrar ahora. Confirme que quiere cerrar la aplicaci\u00f3n cuando le sea preguntado.", 
    "\n      If you have concerns about your proctoring session results, contact your course team.\n    ": "\nSi tiene dudas sobre los resultados de su sesi\u00f3n supervisada, comun\u00edquese con el equipo del curso.", 
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\nSi tiene una discapacidad,\npuede ser eligible para un permiso de tiempo adicional en los ex\u00e1menes cronometrados.\nSolicite informaci\u00f3n sobre tiempo adicional al equipo del curso.", 
    "\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\nSi tiene preguntas sobre el estado de los resultados de su examen supervisado, cont\u00e1ctese con el equipo de apoyo de %(platform_name)s.", 
    "\n      If you have questions about the status of your requirements for course credit, contact %(platform_name)s Support.\n    ": "\nSi tiene preguntas sobre su estado con los requisitos para cr\u00e9dito acad\u00e9mico en este curso, cont\u00e1ctese con el equipo de ayuda para %(platform_name)s.", 
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\nConfirme que haya seleccionado \"Enviar\" para cada problema antes de enviar el examen completo..", 
    "\n      Practice exams do not affect your grade or your credit eligibility.\n      You have completed this practice exam and can continue with your course work.\n    ": "\nLos ex\u00e1menes de pr\u00e1ctica no afectan su calificaci\u00f3n ni su elegibilidad para cr\u00e9dito.\nHa completado este examen de pr\u00e1ctica y puede seguir con el curso.", 
    "\n      The due date for this exam has passed\n    ": "\nLa fecha l\u00edmite para este examen ha pasado.", 
    "\n      There was a problem with your practice proctoring session\n    ": "\nHubo un problema con su sesi\u00f3n supervisada de pr\u00e1ctica.", 
    "\n      This exam is proctored\n    ": "\nEste examen es supervisado", 
    "\n      To be eligible for course credit or for a MicroMasters credential, you must pass the proctoring review for this exam.\n    ": "\nPara ser elegible para cr\u00e9dito acad\u00e9mico o una credencial MicroMasters, debe aprobar la revisi\u00f3n de supervisi\u00f3n para este examen.", 
    "\n      To view your exam questions and responses, select <strong>View my exam</strong>. The exam's review status is shown in the left navigation pane.\n    ": "\nPara ver las preguntas y respuestas de su examen, seleccione <strong>Ver mi examen</strong>. El estado de revisi\u00f3n del examen se muestra en el panel de navegaci\u00f3n a la izquierda.", 
    "\n      Try a proctored exam\n    ": "\nIntentar un examen supervisado", 
    "\n      View your credit eligibility status on your <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\nRevise el estado de su elegibilidad para cr\u00e9dito en su <a href=\"%(progress_page_url)s\">p\u00e1gina de progreso</a>.", 
    "\n      Yes, end my proctored exam\n    ": "\nS\u00ed, terminar mi examen supervisado", 
    "\n      Yes, submit my timed exam.\n    ": "\nS\u00ed, enviar my examen cronometrado.", 
    "\n      You are eligible to purchase academic credit for this course if you complete all required exams\n      and also achieve a final grade that meets the credit requirements for the course.\n    ": "\nUsted es eligible para comprar cr\u00e9dito acad\u00e9mico en este curso si completa todos los ex\u00e1menes requeridos \ny tambi\u00e9n si logra una nota final que cumpla con los requisitos para cr\u00e9dito en este curso.", 
    "\n      You are no longer eligible for academic credit for this course, regardless of your final grade.\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\nYa no es elegible para cr\u00e9dito acad\u00e9mico en este curso independientemente de cualquier calificaci\u00f3n final que haya logrado.\nSi tiene preguntas sobre el estado de los resultados de su examen supervisado, comun\u00edquese con el equipo de ayuda de %(platform_name)s.", 
    "\n      You have submitted this practice proctored exam\n    ": "\nHa enviado este examen de pr\u00e1ctica supervisado", 
    "\n      You have submitted this proctored exam for review\n    ": "\nHa enviado este examen supervisado para revisi\u00f3n", 
    "\n      Your grade for this timed exam will be immediately available on the <a href=\"%(progress_page_url)s\">Progress</a> page.\n    ": "\nSu calificaci\u00f3n de este examen cronometrado estar\u00e1  disponible inmediatamente en la <a href=\"%(progress_page_url)s\">p\u00e1gina de progreso</a>.", 
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\nEl resultado de su sesi\u00f3n supervisada de pr\u00e1ctica: <b class=\"failure\"> inadecuado </b>", 
    "\n      Your proctoring session ended before you completed this practice exam.\n      You can retry this practice exam if you had problems setting up the online proctoring software.\n    ": "\nSu sesi\u00f3n supervisada termin\u00f3 antes de que completara este examen de pr\u00e1ctica.\nPuede comenzar el examen de nuevo si tuvo problemas iniciando el programa de supervisi\u00f3n online.", 
    "\n      Your proctoring session was reviewed and did not pass requirements\n    ": "\nSu sesi\u00f3n supervisada fue revisada y no cumpli\u00f3 con los requisitos", 
    "\n      Your proctoring session was reviewed and passed all requirements\n    ": "\nSu sesi\u00f3n supervisada fue revisada y cumpli\u00f3 con todos los requisitos", 
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n%(exam_name)s es un examen cronometrado (%(total_time)s)", 
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\nLos siguientes requisitos est\u00e1n en un estado <strong>pendiente</strong> y tienen que ser cumplidos exitosamente antes de que pueda proceder:", 
    "\n    You can take this exam with proctoring only when all prerequisites have been successfully completed. Check your <a href=\"%(progress_page_url)s\">Progress</a>  page to see if prerequisite results have been updated. You can also take this exam now without proctoring, but you will not be eligible for credit.\n    ": "\nSolo puede tomar este examen con supervisi\u00f3n una vez haya cumplido con todos los requisitos. Revise su <a href=\"%(progress_page_url)s\">p\u00e1gina de progreso</a> para ver si los resultados de los requisitos han sido actualizados. En este momento puede tomar este examen sin supervisi\u00f3n, pero no ser\u00e1 elegible para cr\u00e9dito acad\u00e9mico.", 
    "\n    You did not satisfy the following prerequisites:\n    ": "\nNo cumpli\u00f3 los siguientes prerrequisitos:", 
    "\n    You did not satisfy the requirements for taking this exam with proctoring, and are not eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements and your status for each.\n    ": "\nNo cumpli\u00f3 los requisitos para hacer este examen con supervisi\u00f3n, y no es elegible para cr\u00e9dito. Revise su <a href=\"%(progress_page_url)s\">p\u00e1gina de progreso</a> para ver una lista de los requisitos y su estado en cada uno.", 
    "\n    You have not completed the prerequisites for this exam. All requirements must be satisfied before you can take this proctored exam and be eligible for credit. See your <a href=\"%(progress_page_url)s\">Progress</a> page for a list of requirements in the order that they must be completed.\n    ": "\nNo cumpli\u00f3 los requisitos para hacer este examen con supervisi\u00f3n. Es necesario cumplir todos los requisitos para poder tomar este examen supervisado y ser elegible para cr\u00e9dito. Revise su <a href=\"%(progress_page_url)s\">p\u00e1gina de progreso</a> para una lista de los requisitos y el orden en que se tiene que cumplir cada uno.", 
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": "A partir de este momento, debe seguir las <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">reglas de supervisi\u00f3n online</a> para aprobar la revisi\u00f3n de la supervisi\u00f3n para su examen.", 
    " Your Proctoring Session Has Started ": "Su Sesi\u00f3n Supervisada Ha Comenzado", 
    " and {num_of_minutes} minute": "y {num_of_minutes} minuto", 
    " and {num_of_minutes} minutes": "y {num_of_minutes} minutos", 
    " to complete and submit the exam.": "para completar y enviar el examen.", 
    "%(earned)s/%(possible)s point (graded)": [
      "%(earned)s/%(possible)s punto (calificable)", 
      "%(earned)s/%(possible)s puntos (calificables)"
    ], 
    "%(earned)s/%(possible)s point (ungraded)": [
      "%(earned)s/%(possible)s punto (no calificable)", 
      "%(earned)s/%(possible)s puntos (no calificables)"
    ], 
    "%(errorCount)s error found in form.": [
      "%(errorCount)s error encontrado en el formulario.", 
      "%(errorCount)s errores encontrados en el formulario."
    ], 
    "%(memberCount)s / %(maxMemberCount)s Member": [
      "%(memberCount)s / %(maxMemberCount)s Miembro", 
      "%(memberCount)s / %(maxMemberCount)s Miembros"
    ], 
    "%(num_points)s point possible (graded)": [
      "%(num_points)s punto posible (calificable)", 
      "%(num_points)s puntos posibles (calificables)"
    ], 
    "%(num_points)s point possible (graded, results hidden)": [
      "%(num_points)s  punto posible (calificable, resultados ocultos)", 
      "%(num_points)s puntos posibles (calificables, resultados ocultos)"
    ], 
    "%(num_points)s point possible (ungraded)": [
      "%(num_points)s punto posible (no calificable)", 
      "%(num_points)s puntos posibles (no calificables)"
    ], 
    "%(num_points)s point possible (ungraded, results hidden)": [
      "%(num_points)s punto posible (no calificable, resultados ocultos)", 
      "%(num_points)s puntos posibles (no calificables, resultados ocultos)"
    ], 
    "%(num_questions)s question": [
      "%(num_questions)s pregunta", 
      "%(num_questions)s preguntas"
    ], 
    "%(num_students)s student": [
      "%(num_students)s estudiante", 
      "%(num_students)s estudiantes"
    ], 
    "%(num_students)s student opened Subsection": [
      "%(num_students)s subsecci\u00f3n abierta para el estudiante", 
      "%(num_students)s subsecci\u00f3n abierta para los estudiantes"
    ], 
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s seleccionado", 
      "%(sel)s de  %(cnt)s seleccionados"
    ], 
    "%(team_count)s Team": [
      "%(team_count)s Equipo", 
      "%(team_count)s Equipos"
    ], 
    "%(value)s hour": [
      "%(value)s hora", 
      "%(value)s horas"
    ], 
    "%(value)s minute": [
      "%(value)s minuto", 
      "%(value)s minutos"
    ], 
    "%(value)s second": [
      "%(value)s segundo", 
      "%(value)s segundos"
    ], 
    "%d day": [
      "%d d\u00eda", 
      "%d d\u00edas"
    ], 
    "%d minute": [
      "%d minuto", 
      "%d minutos"
    ], 
    "%d month": [
      "%d mes", 
      "%d meses"
    ], 
    "%d year": [
      "%d a\u00f1o", 
      "%d a\u00f1os"
    ], 
    "(contains %(student_count)s student)": [
      "(contiene%(student_count)s de estudiantes)", 
      "(contiene %(student_count)s de estudiantes)"
    ], 
    "(required):": "(requerido):", 
    "6 a.m.": "6 a.m.", 
    "6 p.m.": "6 p.m.", 
    "Additional Time (minutes)": "Tiempo adicional (minutos)", 
    "After you select ": "Despu\u00e9s de seleccionar", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Despu\u00e9s de subir nuevos archivos, todos sus archivos subidos anteriormente ser\u00e1n borrados. \u00bfProceder?", 
    "All Unreviewed": "Todos los no revisados", 
    "All Unreviewed Failures": "Todos los fracasos no revisados", 
    "April": "Abril", 
    "Assessment": "Evaluaci\u00f3n", 
    "Assessments": "Evaluaciones", 
    "August": "Agosto", 
    "Available %s": "%s Disponibles", 
    "Back to Full List": "Volver a la lista completa", 
    "Block view is unavailable": "Vista de bloque no disponible", 
    "Can I request additional time to complete my exam?": "\u00bfPuedo pedir tiempo adicional para completar mi examen?", 
    "Cancel": "Cancelar", 
    "Cannot Start Proctored Exam": "No se puede Iniciar el Examen Supervisado", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Los cambios en los pasos que no est\u00e1n seleccionados como parte de la tarea no ser\u00e1n guardados.", 
    "Check the box to remove %(count)s flag.": [
      "Marca la casilla para remover %(count)s marca de denuncio.", 
      "Marca la casilla para remover %(count)s marcas de denuncio."
    ], 
    "Check the box to remove %(totalFlags)s flag.": [
      "Marca la casilla para remover %(totalFlags)s marca de denuncio.", 
      "Marca la casilla para remover %(totalFlags)s marcas de denuncio."
    ], 
    "Choose": "Elegir", 
    "Choose a Date": "Elija una fecha", 
    "Choose a Time": "Elija una hora", 
    "Choose a time": "Elija una hora", 
    "Choose all": "Selecciona todos", 
    "Chosen %s": "%s elegidos", 
    "Click to choose all %s at once.": "Haga clic para seleccionar todos los %s de una vez", 
    "Click to remove all chosen %s at once.": "Haz clic para eliminar todos los %s elegidos", 
    "Close": "Cerrar", 
    "Contains {count} group": [
      "Contiene {count} grupo", 
      "Contiene {count} grupos"
    ], 
    "Continue Exam Without Proctoring": "Continuar Examen Sin Supervisi\u00f3n", 
    "Continue to Verification": "Continuar a la verificaci\u00f3n", 
    "Continue to my practice exam": "Continuar a mi examen de pr\u00e1ctica", 
    "Continue to my proctored exam. I want to be eligible for credit.": "Continuar a mi examen supervisado. Quiero ser elegible para cr\u00e9dito.", 
    "Could not retrieve download url.": "No se pudo recuperar la url de descarga.", 
    "Could not retrieve upload url.": "No se pudo recuperar la url de subida.", 
    "Couldn't Save This Assignment": "No se ha podido salvar esta tarea.", 
    "Course": [
      "Curso", 
      "Cursos"
    ], 
    "Course Id": "Id de Curso", 
    "Created": "Creado", 
    "Criterion Added": "Criterio a\u00f1adido.", 
    "Criterion Deleted": "Criterio borrado.", 
    "December": "Diciembre", 
    "Declined": "Negado", 
    "Describe ": "Describir", 
    "Do you want to upload your file before submitting?": "Quieres subir tu archivo antes de enviarlo ?", 
    "Doing so means that you are no longer eligible for academic credit.": "Hacer esto significa que ya no ser\u00e1 elegible para cr\u00e9dito acad\u00e9mico.", 
    "Download Software Clicked": "'Descargar aplicaci\u00f3n' seleccionado", 
    "End My Exam": "Finalizar mi examen", 
    "Error": "Error", 
    "Error getting the number of ungraded responses": "Error al obtener el n\u00famero de respuestas no calificadas.", 
    "Failed Proctoring": "Supervisi\u00f3n fallida", 
    "February": "Febrero", 
    "Feedback available for selection.": "Comentarios disponibles para esta selecci\u00f3n.", 
    "File size must be 10MB or less.": "Tama\u00f1o del archivo debe ser de 10MB como m\u00e1ximo.", 
    "File type is not allowed.": "Tipo de archivo no permitido.", 
    "File types can not be empty.": "Tipo de archivo no puede ser vac\u00edo.", 
    "Filter": "Filtro", 
    "Final Grade Received": "Calificaci\u00f3n final recibida", 
    "Go Back": "Volver Atr\u00e1s", 
    "Heading 3": "Encabezado 3", 
    "Heading 4": "Encabezado 4", 
    "Heading 5": "Encabezado 5", 
    "Heading 6": "Encabezado 6", 
    "Hide": "Esconder", 
    "I am ready to start this timed exam,": "Estoy listo/a para empezar este examen cronometrado,", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Si abandona esta p\u00e1gina sin guardar o enviar su respuesta, perder\u00e1 todo el trabajo realizado en la respuesta.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Si abandona esta p\u00e1gina sin enviar su trabajo, perder\u00e1 todos los cambios realizados.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Si abandona esta p\u00e1gina sin enviar su auto evaluaci\u00f3n, perder\u00e1 todos los cambios realizados.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Si abandona esta p\u00e1gina sin enviar su evaluaci\u00f3n, se perder\u00e1n todos los cambios realizados.", 
    "Is Sample Attempt": "Es un intento de muestra", 
    "January": "Enero", 
    "July": "Julio", 
    "June": "Junio", 
    "List of Open Assessments is unavailable": "Lista de evaluaciones abiertas no disponible", 
    "Load next {num_items} result": [
      "Cargar {num_items} resultado", 
      "Cargar los siguientes {num_items} resultados"
    ], 
    "March": "Marzo", 
    "May": "Mayo", 
    "Midnight": "Medianoche", 
    "Must be a Staff User to Perform this request.": "Hay que ser un usuario del equipo para cumplir esta petici\u00f3n.", 
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
    "One or more rescheduling tasks failed.": "Una o m\u00e1s tareas de re-programaci\u00f3n fall\u00f3.", 
    "Option Deleted": "Opci\u00f3n borrada.", 
    "Paragraph": "P\u00e1rrafo", 
    "Passed Proctoring": "Supervisi\u00f3n aprobada", 
    "Peer": "Par", 
    "Pending Session Review": "Revisi\u00f3n de sesi\u00f3n pendiente", 
    "Please correct the outlined fields.": "Por favor corrija los campos resaltados.", 
    "Please wait": "Por favor espere", 
    "Practice Exam Completed": "Examen de pr\u00e1ctica completado", 
    "Practice Exam Failed": "Examen de pr\u00e1ctica no aprobado", 
    "Preformatted": "Preformateado", 
    "Proctored Option Available": "Opci\u00f3n supervisada disponible", 
    "Proctored Option No Longer Available": "La opci\u00f3n supervisado ya no est\u00e1 disponible", 
    "Proctoring Session Results Update for {course_name} {exam_name}": "Actualizaci\u00f3n de resultados de sesi\u00f3n supervisada para {course_name} {exam_name}", 
    "Ready To Start": "Listo para comenzar", 
    "Ready To Submit": "Listo para enviar", 
    "Rejected": "Rechazado", 
    "Remove": "Eliminar", 
    "Remove all": "Eliminar todos", 
    "Retry Verification": "Reenviar verificaci\u00f3n", 
    "Review Policy Exception": "Revisar excepci\u00f3n a la pol\u00edtica", 
    "Saving...": "Guardando...", 
    "Second Review Required": "Segunda revisi\u00f3n requerida", 
    "Self": "Auto", 
    "September": "Septiembre", 
    "Server error.": "Error en el servidor.", 
    "Show": "Mostrar", 
    "Show Comment (%(num_comments)s)": [
      "Mostrar comentario (%(num_comments)s)", 
      "Mostrar comentarios (%(num_comments)s)"
    ], 
    "Showing first response": [
      "Se muestra la primera respuesta", 
      "Se muestra primeras {numResponses} respuestas"
    ], 
    "Staff": "Equipo del Curso", 
    "Start Proctored Exam": "Iniciar Examen Supervisado", 
    "Start System Check": "Empezar chequeo del sistema", 
    "Started": "Inici\u00f3", 
    "Status of Your Response": "Estado de su respuesta", 
    "Submitted": "Enviado", 
    "Take this exam without proctoring.": "Tomar este examen sin supervisi\u00f3n.", 
    "Taking As Open Exam": "Tomando como examen abierto", 
    "Taking As Proctored Exam": "Tomando como examen supervisado", 
    "Taking as Proctored": "Tomando como examen supervisado", 
    "The display of ungraded and checked out responses could not be loaded.": "La lista de respuestas marcadas y no calificadas no pudo ser cargada.", 
    "The following file types are not allowed: ": "Los siguientes tipos de archivos son soportados:", 
    "The server could not be contacted.": "No se ha podido contactar con el servidor.", 
    "The staff assessment form could not be loaded.": "La valoraci\u00f3n del equipo del curso no pudo ser cargada.", 
    "The submission could not be removed from the grading pool.": "La entrega no pudo ser eliminada de la lista de evaluaciones", 
    "There was an error when trying to add learners:": [
      "Hubo un error tratando de a\u00f1adir estudiantes:", 
      "{numErrors} estudiantes no pudieron ser a\u00f1adidos a este cohorte."
    ], 
    "This annotation has %(count)s flag.": [
      "Esta anotaci\u00f3n tiene %(count)s marca de denuncio.", 
      "Esta anotaci\u00f3n tiene %(count)s marcas de denuncio."
    ], 
    "This assessment could not be submitted.": "Esta revisi\u00f3n no pudo ser enviada.", 
    "This exam has a time limit associated with it.": "Esta examen tiene un l\u00edmite de tiempo.", 
    "This feedback could not be submitted.": "Este comentario no pudo ser enviado.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta es la lista de %s disponibles. Puede elegir algunos seleccion\u00e1ndolos en la caja inferior y luego haciendo clic en la flecha \"Elegir\" que hay entre las dos cajas.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta es la lista de los %s elegidos. Puede elmininar algunos seleccion\u00e1ndolos en la caja inferior y luego haciendo click en la flecha \"Eliminar\" que hay entre las dos cajas.", 
    "This problem could not be saved.": "Este problema no pudo ser guardado.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "Este problema ya ha sido liberado. Cualquier cambio en el mismo se aplicar\u00e1 solo a los env\u00edo futuros.", 
    "This response could not be saved.": "Esta respuesta no pudo ser guardada.", 
    "This response could not be submitted.": "Esta respuesta no pudo ser enviada.", 
    "This response has been saved but not submitted.": "La respuesta ha sido guardada, pero no enviada.", 
    "This response has not been saved.": "Esta respuesta no ha sido guardada.", 
    "This section could not be loaded.": "Esta secci\u00f3n no pudo ser cargada.", 
    "Thumbnail view of ": "Vista miniatura de", 
    "Timed Exam": "Examen cronometrado", 
    "Timed Out": "Tiempo agotado", 
    "To pass this exam, you must complete the problems in the time allowed.": "Para aprobar este examen, hay que completar los problemas durante el tiempo permitido.", 
    "Today": "Hoy", 
    "Tomorrow": "Ma\u00f1ana", 
    "Total Responses": "Total de respuestas", 
    "Training": "Entrenamiento", 
    "Try this practice exam again": "Comenzar este examen de pr\u00e1ctica nuevamente", 
    "Type into this box to filter down the list of available %s.": "Escriba en este cuadro para filtrar la lista de %s disponibles", 
    "Unable to load": "No se ha podido cargar", 
    "Unexpected server error.": "Ocurri\u00f3 un error inesperado en el servidor.", 
    "Ungraded Practice Exam": "Examen de pr\u00e1ctica no calificado", 
    "Unit Name": "Nombre de la unidad", 
    "Units": "Unidades", 
    "Unnamed Option": "Opci\u00f3n sin nombre", 
    "Used in {count} location": [
      "Usado en {count} ubicaci\u00f3n", 
      "Usado en {count} ubicaciones"
    ], 
    "Verified": "Verificado", 
    "View my exam": "Ver mi examen", 
    "Viewing %s course": [
      "Viendo  %s curso", 
      "Viendo %s cursos"
    ], 
    "Waiting": "Esperando", 
    "Warning": "Atenci\u00f3n:", 
    "Yesterday": "Ayer", 
    "You can also retry this practice exam": "Tambi\u00e9n puede comenzar este examen de pr\u00e1ctica nuevamente", 
    "You can upload files with these file types: ": "Puedes subir archivos de estos tipos:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Ha a\u00f1adido un nuevo criterio. Deber\u00e1 seleccionar una opci\u00f3n para el criterio que se usar\u00e1 en el paso de entrenamiento del estudiante.  Para hacer esto, haga clic en la pesta\u00f1a de Configuraci\u00f3n. ", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Ha borrado un criterio. El criterio ha sido removido de los ejemplos de respuesta en el paso de entrenamiento del estudiante.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Has eliminado todas las opciones para este criterio. El criterio ha sido removido de las respuestas de ejemplo en el paso de entrenamiento del estudiante.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Has borrado esta opci\u00f3n. Esta opci\u00f3n ha sido removida del criterio en el ejemplo de respuestas en el paso de entrenamiento del estudiante. Es posible que tenga que seleccionar una nueva opci\u00f3n para el criterio.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Ha seleccionado una acci\u00f3n y no hs hecho ning\u00fan cambio en campos individuales. Probablemente est\u00e9 buscando el bot\u00f3n Ejecutar en lugar del bot\u00f3n Guardar.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Ha seleccionado una acci\u00f3n, pero no ha guardado los cambios en los campos individuales todav\u00eda. Pulse OK para guardar. Tendr\u00e1 que volver a ejecutar la acci\u00f3n.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tiene cambios sin guardar en campos editables individuales. Si ejecuta una acci\u00f3n, los cambios no guardados se perder\u00e1n.", 
    "You must provide a learner name.": "Debe ingresar un nombre.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Est\u00e1 a punto de subir su respuesta para esta tarea. Despu\u00e9s de subirla, no podr\u00e1 cambiarla o subir una nueva respuesta.", 
    "Your file ": "Su archivo", 
    "about %d hour": [
      "cerca de %d hora", 
      "cerca de %d horas"
    ], 
    "active proctored exams": "ex\u00e1menes supervisados activos", 
    "could not determine the course_id": "No se pudo determinar la ID del curso", 
    "courses with active proctored exams": "cursos con ex\u00e1menes supervisados activos", 
    "internally reviewed": "revisado internamente", 
    "one letter Friday\u0004F": "V", 
    "one letter Monday\u0004M": "L", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "D", 
    "one letter Thursday\u0004T": "J", 
    "one letter Tuesday\u0004T": "M", 
    "one letter Wednesday\u0004W": "M", 
    "pending": "pendiente", 
    "practice": "pr\u00e1ctica", 
    "proctored": "supervisado", 
    "satisfactory": "adecuado", 
    "there is currently {numVotes} vote": [
      "Actualmente hay {numVotes} voto", 
      "Actualmente hay {numVotes} votos"
    ], 
    "timed": "cronometrado", 
    "unsatisfactory": "inadecuado", 
    "you have less than a minute remaining": "Queda menos de un minuto", 
    "you have {remaining_time} remaining": "usted tiene {remaining_time} para terminar", 
    "you will have ": "Tendr\u00e1", 
    "your course": "su curso", 
    "{numMoved} learner was moved from {prevCohort}": [
      "{numMoved} estudiante fue movido desde {prevCohort}", 
      "{numMoved} estudiantes fueron movidos desde {prevCohort}"
    ], 
    "{numPreassigned} learner was pre-assigned for this cohort. This learner will automatically be added to the cohort when they enroll in the course.": [
      "{numPreassigned} estudiante fue pre-asignado para este cohorte. Este estudiante ser\u00e1 a\u00f1adido autom\u00e1ticamente al cohorte cuando se inscriba en el curso.", 
      "{numPreassigned} estudiantes fueron pre-asignados para este cohorte. Estos estudiantes ser\u00e1n a\u00f1adidos autom\u00e1ticamente al cohorte cuando se inscriban en el curso."
    ], 
    "{numPresent} learner was already in the cohort": [
      "{numPresent} estudiante ya estaba en el cohorte", 
      "{numPresent} estudiantes ya estaban en el cohorte"
    ], 
    "{numResponses} other response": [
      "{numResponses} otra respuesta", 
      "{numResponses} otras respuestas"
    ], 
    "{numResponses} response": [
      "{numResponses} respuesta", 
      "{numResponses} respuestas"
    ], 
    "{numUsersAdded} learner has been added to this cohort. ": [
      "{numUsersAdded} estudiante ha sido a\u00f1adido a este cohorte. ", 
      "{numUsersAdded} estudiantes han sido a\u00f1adidos a este cohorte. "
    ], 
    "{numVotes} Vote": [
      "{numVotes} Voto", 
      "{numVotes} Votos"
    ], 
    "{num_of_hours} hour": "{num_of_hours} hora", 
    "{num_of_hours} hours": "{num_of_hours} horas", 
    "{num_of_minutes} minute": "{num_of_minutes} minuto", 
    "{num_of_minutes} minutes": "{num_of_minutes} minutos", 
    "{total_results} result": [
      "{total_results} resultado", 
      "{total_results} resultados"
    ]
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
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j \\d\\e F", 
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
    "YEAR_MONTH_FORMAT": "F \\d\\e Y"
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

