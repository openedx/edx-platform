

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
    "\n          Step 2\n        ": "\n          Paso 2\n        ",
    "\n          Step 3\n        ": "\n          Paso 3\n        ",
    "\n        Create your onboarding profile for faster access in the future\n      ": "\nCrear perfil de incorporaci\u00f3n para un acceso m\u00e1s r\u00e1pido en el futuro",
    "\n        Establish your identity with the proctoring system to take a proctored exam\n      ": "\n       Establecer la identidad con el sistema de supervision para tomar el examen supervisado\n      ",
    "\n        Hello %(username)s,\n    ": "\n        Hola %(username)s,\n    ",
    "\n        The result will be visible after <strong id=\"wait_deadline\"> Loading... </strong>\n    ": "\nEl resultado ser\u00e1 visible despu\u00e9s de <strong id=\"wait_deadline\">Cargar...</strong>",
    "\n        To appeal your proctored exam results, please reach out with any relevant information\n        about your exam at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\nPara apelar los resultados de su examen supervisado, comun\u00edquese con cualquier informaci\u00f3n relevante sobre su examen en <a href=\"%(contact_url)s\">%(contact_url_text)s</a> .",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and the\n        course team has identified one or more violations of the proctored exam rules. Examples\n        of issues that may result in a rules violation include browsing\n        the internet, blurry or missing photo identification, using a phone,\n        or getting help from another person. As a result of the identified issue(s),\n        you did not successfully meet the proctored exam requirements.\n    ": "\nSu examen supervisado \"%(exam_name)s\" en <a href=\"%(course_url)s\">%(course_name)s</a>\" fue revisado y el equipo del curso identific\u00f3 una o m\u00e1s violaciones de las reglas del examen supervisado. Los ejemplos de problemas que pueden resultar en una violaci\u00f3n de las reglas incluyen navegar por Internet, una identificaci\u00f3n con foto borrosa o faltante, usar un tel\u00e9fono u obtener ayuda de otra persona. Como resultado de los problema(s) identificado, no cumpli\u00f3 satisfactoriamente con los requisitos del examen supervisado.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and you\n        met all proctoring requirements.\n    ": "\nSe revis\u00f3 su examen supervisado \"%(exam_name)s\" en <a href=\"%(course_url)s\">%(course_name)s</a> y cumpli\u00f3 con todos los requisitos de supervisi\u00f3n.",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was submitted\n        successfully and will now be reviewed to ensure all exam\n        rules were followed. You should receive an email with your exam\n        status within 5 business days.\n    ": "\nSu examen supervisado \"%(exam_name)s\" en <a href=\"%(course_url)s\">%(course_name)s</a> se envi\u00f3 correctamente y ahora se revisar\u00e1 para garantizar que se hayan seguido todas las reglas del examen. Deber\u00eda recibir un correo electr\u00f3nico con el estado de su examen dentro de los 5 d\u00edas h\u00e1biles.",
    "\n      Why this is important to you:\n    ": "\nPor qu\u00e9 esto es importante para usted:",
    "\n    If you have any questions about your results, you can reach out at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\nSi tiene alguna pregunta sobre sus resultados, puede comunicarse con <a href=\"%(contact_url)s\">%(contact_url_text)s</a> .",
    "\n    Proctoring onboarding exam\n  ": "\n  Examen de ingreso supervisado\n  ",
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s seleccionado/a",
      "%(sel)s de %(cnt)s seleccionados/as"
    ],
    "(required):": "(requerido):",
    "6 a.m.": "6 AM",
    "6 p.m.": "6 PM",
    "Additional Time (minutes)": "Tiempo adicional (minutos)",
    "All Unreviewed": "Todo sin revisar",
    "All Unreviewed Failures": "Todas las fallas no revisadas",
    "April": "Abril",
    "Are you sure you want to delete the following file? It cannot be restored.\nFile: ": "\u00bfEst\u00e1 seguro de que desea eliminar el siguiente archivo? No se puede restaurar. Archivo:",
    "Assessment": "Evaluaci\u00f3n",
    "Assessments": "Evaluaciones",
    "August": "Agosto",
    "Available %s": "%s disponibles",
    "Back to Full List": "Volver a la lista completa",
    "Block view is unavailable": "La vista de bloque no est\u00e1 disponible",
    "Cancel": "Cancelar",
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Los cambios en los pasos que no se seleccionen como parte de la tarea no se guardar\u00e1n.",
    "Choose": "Seleccionar",
    "Choose a Date": "Seleccione una Fecha",
    "Choose a Time": "Seleccione una Hora",
    "Choose a time": "Elija una hora",
    "Choose all": "Seleccionar todos/as",
    "Chosen %s": "%s seleccionados/as",
    "Click to choose all %s at once.": "Haga click para seleccionar todos/as los/as %s.",
    "Click to remove all chosen %s at once.": "Haga clic para deselecionar todos/as los/as %s.",
    "Close": "Cerrar",
    "Confirm": "Confirmar",
    "Confirm Delete Uploaded File": "Confirmar eliminar archivo cargado",
    "Confirm Grade Team Submission": "Confirmar el env\u00edo del equipo de calificaciones",
    "Confirm Submit Response": "Confirmar enviar respuesta",
    "Could not load teams information.": "No se pudo cargar la informaci\u00f3n de los equipos.",
    "Could not retrieve download url.": "No se pudo recuperar la URL de descarga.",
    "Could not retrieve upload url.": "No se pudo recuperar la URL de carga.",
    "Course Id": "Identificaci\u00f3n del curso",
    "Created": "Creado",
    "Criterion Added": "Criterio agregado",
    "Criterion Deleted": "Criterio Eliminado",
    "December": "Diciembre",
    "Declined": "Rechazado",
    "Demo the new Grading Experience": "Demostraci\u00f3n de la nueva experiencia de calificaci\u00f3n",
    "Describe ": "Describir",
    "Download Software Clicked": "Software de descarga hecho clic",
    "End My Exam": "Finalizar mi examen",
    "Error": "Error",
    "Error getting the number of ungraded responses": "Error al obtener el n\u00famero de respuestas sin calificar",
    "Error when looking up username": "Error al buscar nombre de usuario",
    "Error while fetching student data.": "Error al obtener los datos del alumno.",
    "Errors detected on the following tabs: ": "Errores detectados en las siguientes pesta\u00f1as:",
    "Failed Proctoring": "Supervisi\u00f3n fallida",
    "Failed to clone rubric": "No se pudo clonar la r\u00fabrica",
    "February": "Febrero",
    "Feedback available for selection.": "Comentarios disponibles para la selecci\u00f3n.",
    "File types can not be empty.": "Los tipos de archivo no pueden estar vac\u00edos.",
    "File upload failed: unsupported file type. Only the supported file types can be uploaded. If you have questions, please reach out to the course team.": "Error al cargar el archivo: tipo de archivo no compatible. Solo se pueden cargar los tipos de archivos admitidos. Si tiene preguntas, comun\u00edquese con el equipo del curso.",
    "Filter": "Filtro",
    "Final Grade Received": "Calificaci\u00f3n final recibida",
    "Go Back": "Volver",
    "Grade Status": "Estado de calificaci\u00f3n",
    "Heading 3": "T\u00edtulo 3",
    "Heading 4": "T\u00edtulo 4",
    "Heading 5": "T\u00edtulo 5",
    "Heading 6": "T\u00edtulo 6",
    "Hide": "Ocultar",
    "However, {overwritten_count} of these students have received a grade through the staff grade override tool already.": "Sin embargo, {overwritten_count} de estos estudiantes ya han recibido una calificaci\u00f3n a trav\u00e9s de la herramienta de anulaci\u00f3n de calificaciones del personal.",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Si abandona esta p\u00e1gina sin guardar o enviar su respuesta, perder\u00e1 todo el trabajo que haya realizado en la respuesta.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Si sale de esta p\u00e1gina sin enviar su evaluaci\u00f3n por pares, perder\u00e1 todo el trabajo que haya realizado.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Si abandona esta p\u00e1gina sin enviar su autoevaluaci\u00f3n, perder\u00e1 todo el trabajo que haya realizado.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Si abandona esta p\u00e1gina sin enviar su evaluaci\u00f3n del personal, perder\u00e1 todo el trabajo que haya realizado.",
    "Individual file size must be {max_files_mb}MB or less.": "El tama\u00f1o del archivo individual debe ser {max_files_mb} MB o menos.",
    "Is Resumable": "es reanudable",
    "Is Sample Attempt": "Es un intento de muestra",
    "January": "Enero",
    "July": "Julio",
    "June": "Junio",
    "List of Open Assessments is unavailable": "La lista de evaluaciones abiertas no est\u00e1 disponible",
    "March": "Marzo",
    "May": "Mayo",
    "Midnight": "Medianoche",
    "Multiple teams returned for course": "M\u00faltiples equipos regresaron para el curso",
    "Noon": "Mediod\u00eda",
    "Not Selected": "No seleccionado",
    "Note: You are %s hour ahead of server time.": [
      "Nota: Ud. se encuentra en una zona horaria que est\u00e1 %s hora adelantada respecto a la del servidor.",
      "Nota: Ud. se encuentra en una zona horaria que est\u00e1 %s horas adelantada respecto a la del servidor."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: Ud. se encuentra en una zona horaria que est\u00e1 %s hora atrasada respecto a la del servidor.",
      "Nota: Ud. se encuentra en una zona horaria que est\u00e1 %s horas atrasada respecto a la del servidor."
    ],
    "November": "Noviembre",
    "Now": "Ahora",
    "October": "Octubre",
    "Onboarding Expired": "Incorporaci\u00f3n caducada",
    "Onboarding Failed": "Error de incorporaci\u00f3n",
    "Onboarding Missing": "Falta incorporaci\u00f3n",
    "Onboarding Pending": "Incorporaci\u00f3n pendiente",
    "Onboarding status question": "Pregunta sobre el estado de incorporaci\u00f3n",
    "One or more rescheduling tasks failed.": "Una o m\u00e1s tareas de reprogramaci\u00f3n fallaron.",
    "Option Deleted": "Opci\u00f3n eliminada",
    "Paragraph": "P\u00e1rrafo",
    "Passed Proctoring": "Prueba supervisada",
    "Peer": "Par",
    "Peer Responses Received": "Respuestas de compa\u00f1eros recibidas",
    "Peers Assessed": "Compa\u00f1eros evaluados",
    "Pending Session Review": "Revisi\u00f3n de sesi\u00f3n pendiente",
    "Please wait": "Espere por favor",
    "Practice Exam Completed": "Examen de pr\u00e1ctica completado",
    "Practice Exam Failed": "Examen de pr\u00e1ctica fallido",
    "Preformatted": "Preformateado",
    "Problem cloning rubric": "R\u00fabrica de clonaci\u00f3n de problemas",
    "Proctored Option Available": "Opci\u00f3n supervisada disponible",
    "Proctored Option No Longer Available": "La opci\u00f3n supervisada ya no est\u00e1 disponible",
    "Proctored exam {exam_name} in {course_name} for user {username}": "Examen supervisado {exam_name} en {course_name} para el usuario {username}",
    "Proctoring Results For {course_name} {exam_name}": "Resultados de supervisi\u00f3n para {course_name} {exam_name}",
    "Proctoring Review In Progress For {course_name} {exam_name}": "Revisi\u00f3n de supervisi\u00f3n en curso para {course_name} {exam_name}",
    "Ready To Start": "Listo para empezar",
    "Ready To Submit": "Listo para enviar",
    "Ready to Resume": "Listo para reanudar",
    "Refresh": "Actualizar",
    "Rejected": "Rechazado",
    "Remove": "Eliminar",
    "Remove all": "Eliminar todos/as",
    "Resumed": "reanudado",
    "Retry my exam": "Reintentar mi examen",
    "Review Policy Exception": "Excepci\u00f3n de pol\u00edtica de revisi\u00f3n",
    "Save Unsuccessful": "Guardado sin \u00e9xito",
    "Saving...": "Guardando...",
    "Second Review Required": "Segunda revisi\u00f3n requerida",
    "Self": "Auto",
    "September": "Setiembre",
    "Server error.": "Error del Servidor.",
    "Show": "Mostrar",
    "Staff": "Personal",
    "Staff Grader": "Calificador de personal",
    "Staff assessment": "Evaluaci\u00f3n del personal",
    "Started": "Iniciado",
    "Status of Your Response": "Estado de su respuesta",
    "Submitted": "Presentado",
    "Taking As Open Exam": "Examen abierto",
    "Taking As Proctored Exam": "Tomando como examen supervisado",
    "Taking as Proctored": "Tomando como supervisado",
    "The \"{name}\" problem is configured to require a minimum of {min_grades} peer grades, and asks to review {min_graded} peers.": "El problema \"{name}\" est\u00e1 configurado con un m\u00ednimo de {min_grades} calificaciones de compa\u00f1eros y solicita revisar al menos a {min_graded} compa\u00f1eros.",
    "The display of ungraded and checked out responses could not be loaded.": "No se pudo cargar la visualizaci\u00f3n de las respuestas no calificadas y desprotegidas.",
    "The following file types are not allowed: ": "Los siguientes tipos de archivos no est\u00e1n permitidos:",
    "The maximum number files that can be saved is ": "El n\u00famero m\u00e1ximo de archivos que se pueden guardar es",
    "The server could not be contacted.": "No se pudo contactar al servidor.",
    "The staff assessment form could not be loaded.": "No se pudo cargar el formulario de evaluaci\u00f3n del personal.",
    "The submission could not be removed from the grading pool.": "El env\u00edo no se pudo eliminar del grupo de calificaci\u00f3n.",
    "There are currently {stuck_learners} learners in the waiting state, meaning they have not yet met all requirements for Peer Assessment. ": "Actualmente hay {stuck_learners} alumnos en estado de espera, lo que significa que a\u00fan no han cumplido con todos los requisitos para la evaluaci\u00f3n por pares.",
    "This ORA has already been released. Changes will only affect learners making new submissions. Existing submissions will not be modified by this change.": "Este ORA ya ha sido publicado. Los cambios solo afectar\u00e1n a los alumnos que realicen nuevos env\u00edos. Las presentaciones existentes no se ver\u00e1n modificadas por este cambio.",
    "This assessment could not be submitted.": "Esta evaluaci\u00f3n no se pudo enviar.",
    "This feedback could not be submitted.": "No se pudo enviar este comentario.",
    "This grade will be applied to all members of the team. Do you want to continue?": "Esta nota se aplicar\u00e1 a todos los miembros del equipo. \u00bfQuieres continuar?",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta es la lista de %s disponibles. Puede elegir algunos/as seleccion\u00e1ndolos/as en el cuadro de abajo y luego haciendo click en la flecha \"Seleccionar\" ubicada entre las dos listas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta es la lista de %s seleccionados. Puede deseleccionar algunos de ellos activ\u00e1ndolos en la lista de abajo y luego haciendo click en la flecha \"Eliminar\" ubicada entre las dos listas.",
    "This problem could not be saved.": "Este problema no se pudo guardar.",
    "This response could not be saved.": "Esta respuesta no se pudo guardar.",
    "This response could not be submitted.": "No se pudo enviar esta respuesta.",
    "This response has been saved but not submitted.": "Esta respuesta ha sido guardada pero no enviada.",
    "This response has not been saved.": "Esta respuesta no se ha guardado.",
    "This section could not be loaded.": "No se pudo cargar esta secci\u00f3n.",
    "Thumbnail view of ": "Vista en miniatura de",
    "Time Spent On Current Step": "Tiempo empleado en el paso actual",
    "Timed Exam": "Examen cronometrado",
    "Timed Out": "Caducado",
    "Today": "Hoy",
    "Tomorrow": "Ma\u00f1ana",
    "Total Responses": "Respuestas totales",
    "Training": "Capacitaci\u00f3n",
    "Type into this box to filter down the list of available %s.": "Escriba en esta caja para filtrar la lista de %s disponibles.",
    "Unable to load": "No puede cargar",
    "Unexpected server error.": "Error inesperado del servidor.",
    "Ungraded Practice Exam": "Examen de pr\u00e1ctica sin calificar",
    "Unit Name": "Nombre de la unidad",
    "Units": "Unidades",
    "Unnamed Option": "Opci\u00f3n sin nombre",
    "User lookup failed": "B\u00fasqueda de usuario fallida",
    "Username": "Nombre de usuario",
    "Verified": "Verificado",
    "View and grade responses": "Ver y calificar las respuestas",
    "Waiting": "Esperando",
    "Warning": "Advertencia",
    "Yesterday": "Ayer",
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Assessment Steps tab.": "Has a\u00f1adido un criterio. Deber\u00e1 seleccionar una opci\u00f3n para el criterio en el paso Capacitaci\u00f3n del alumno. Para hacer esto, haga clic en la pesta\u00f1a Pasos de evaluaci\u00f3n.",
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Ha eliminado un criterio. El criterio se elimin\u00f3 de las respuestas de ejemplo en el paso Capacitaci\u00f3n del alumno.",
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Ha eliminado todas las opciones para este criterio. El criterio se elimin\u00f3 de las respuestas de muestra en el paso Capacitaci\u00f3n del alumno.",
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Ha eliminado una opci\u00f3n. Esa opci\u00f3n se elimin\u00f3 de su criterio en las respuestas de muestra en el paso Capacitaci\u00f3n del alumno. Es posible que deba seleccionar una nueva opci\u00f3n para el criterio.",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Ha seleccionado una acci\u00f3n y no ha realizado ninguna modificaci\u00f3n de campos individuales. Es probable que deba usar el bot\u00f3n 'Ir'  y no el bot\u00f3n 'Grabar'.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Ha seleccionado una acci\u00f3n pero todav\u00eda no ha grabado sus cambios en campos individuales. Por favor haga click en Ok para grabarlos. Luego necesitar\u00e1 re-ejecutar la acci\u00f3n.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tiene modificaciones sin guardar en campos modificables individuales. Si ejecuta una acci\u00f3n las mismas se perder\u00e1n.",
    "You must provide a learner name.": "Debe proporcionar un nombre de alumno.",
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Est\u00e1 a punto de enviar su respuesta para esta tarea. Despu\u00e9s de enviar esta respuesta, no puede cambiarla ni enviar una nueva respuesta.",
    "Your file has been deleted or path has been changed: ": "Su archivo ha sido eliminado o la ruta ha sido cambiada:",
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
    "abbrev. month September\u0004Sep": "Set",
    "active proctored exams": "ex\u00e1menes supervisados activos",
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
    "you have {remaining_time} remaining": "tiene {remaining_time} restantes",
    "your course": "su curso"
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
    "DATETIME_FORMAT": "j N Y H:i",
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
    "DATE_FORMAT": "j N Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 0,
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

