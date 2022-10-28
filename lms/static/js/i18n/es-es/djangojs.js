

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
    "\n          Note: As part of the proctored exam setup, you will be asked\n          to verify your identity. Before you begin, make sure you are\n          on a computer with a webcam, and that you have a valid form\n          of photo identification such as a driver\u2019s license or\n          passport.\n        ": "\n         Nota: Como parte de la configuraci\u00f3n del examen supervisado, se te solicitar\u00e1 \n         verificar tu identidad. Antes de empezar, aseg\u00farate de que cuentas con\n         un ordenador con c\u00e1mara web y de que tienes un documento v\u00e1lido\n          de identificaci\u00f3n con tu foto como el carn\u00e9 de conducir o\n          el pasaporte.\n        ",
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n        \u00bfSeguro que quieres hacer este examen sin supervisi\u00f3n?\n      ",
    "\n        Hello %(username)s,\n    ": "\n        Hola, %(username)s:\n    ",
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n      \u00bfSeguro que quieres enviar tu examen cronometrado?\n    ",
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      \u00bfSeguro que quieres terminar tu examen supervisado?\n    ",
    "\n      Your %(platform_name)s account has not yet been activated. To take the proctored exam,\n      you are required to activate your account.\n    ": "\n      No has activado a\u00fan tu cuenta de  %(platform_name)s. Para realizar el examen supervisado,\n      es necesario que actives tu cuenta primero.\n    ",
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s seleccionado",
      "%(sel)s de  %(cnt)s seleccionados"
    ],
    "(required):": "(obligatorio):",
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "April": "Abril",
    "Are you sure you want to delete the following file? It cannot be restored.\nFile: ": "\u00bfSeguro que quieres eliminar el siguiente archivo? No se podr\u00e1 restaurar.\nArchivo:",
    "Assessment": "Tarea",
    "Assessments": "Tareas",
    "August": "Agosto",
    "Available %s": "%s Disponibles",
    "Back to Full List": "Volver a la lista completa",
    "Block view is unavailable": "La vista en bloque no est\u00e1 disponible",
    "Cancel": "Cancelar",
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Los cambios en los pasos que no est\u00e1n seleccionados como parte de la tarea no se guardar\u00e1n.",
    "Choose": "Elegir",
    "Choose a Date": "Elija una Fecha",
    "Choose a Time": "Elija una Hora",
    "Choose a time": "Elija una hora",
    "Choose all": "Selecciona todos",
    "Chosen %s": "%s elegidos",
    "Click to choose all %s at once.": "Haga clic para seleccionar todos los %s de una vez",
    "Click to remove all chosen %s at once.": "Haz clic para eliminar todos los %s elegidos",
    "Confirm": "Confirmar",
    "Confirm Delete Uploaded File": "Confirmar la eliminaci\u00f3n del archivo cargado",
    "Confirm Grade Team Submission": "Confirmar el env\u00edo de la calificaci\u00f3n de equipo",
    "Confirm Submit Response": "Confirmar el env\u00edo de la respuesta",
    "Could not load teams information.": "No ha podido cargarse la informaci\u00f3n de los equipos.",
    "Could not retrieve download url.": "No se ha podido obtener la URL de descarga.",
    "Could not retrieve upload url.": "No se ha podido obtener la URL de carga.",
    "Criterion Added": "Criterio a\u00f1adido",
    "Criterion Deleted": "Criterio eliminado",
    "December": "Diciembre",
    "Demo the new Grading Experience": "Demostraci\u00f3n de la nueva Experiencia de Calificaci\u00f3n",
    "Describe ": "Describir",
    "Enter a valid username or email": "Escribe un nombre de usuario o un correo electr\u00f3nico v\u00e1lido",
    "Error": "Error",
    "Error getting the number of ungraded responses": "Error al obtener el n\u00famero de respuestas sin calificar",
    "Error when looking up username": "Error al buscar el nombre de usuario",
    "Error while fetching student data.": "Error al obtener los datos de los estudiantes.",
    "Errors detected on the following tabs: ": "Errores detectados en las siguientes pesta\u00f1as:",
    "Failed to clone rubric": "No se ha podido clonar la r\u00fabrica",
    "February": "Febrero",
    "Feedback available for selection.": "Retroalimentaci\u00f3n disponible para tu selecci\u00f3n.",
    "File types can not be empty.": "Los tipos de archivo no pueden estar en blanco",
    "File upload failed: unsupported file type. Only the supported file types can be uploaded. If you have questions, please reach out to the course team.": "Error al cargar el archivo: tipo de archivo no admitido. Solo se pueden cargar los tipos de archivos admitidos. Si tienes alguna pregunta, contacta con el equipo del curso.",
    "Filter": "Filtro",
    "Final Grade Received": "Nota final recibida",
    "Grade Status": "Estado de la calificaci\u00f3n",
    "Heading 3": "Encabezado 3",
    "Heading 4": "Encabezado 4",
    "Heading 5": "Encabezado 5",
    "Heading 6": "Encabezado 6",
    "Hide": "Ocultar",
    "However, {overwritten_count} of these students have received a grade through the staff grade override tool already.": "Sin embargo, {overwritten_count} de estos estudiantes ya han recibido una calificaci\u00f3n a trav\u00e9s de la herramienta de sobrescritura de calificaci\u00f3n por el equipo docente.",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Si abandonas esta p\u00e1gina sin guardar o enviar tu respuesta, perder\u00e1s todo el trabajo que hayas realizado en la respuesta.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Si abandonas esta p\u00e1gina sin enviar tu evaluaci\u00f3n por pares, perder\u00e1s todo el trabajo que hayas realizado.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Si abandonas esta p\u00e1gina sin enviar tu autoevaluaci\u00f3n, perder\u00e1s todo el trabajo que hayas realizado.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Si abandonas esta p\u00e1gina sin enviar tu evaluaci\u00f3n, perder\u00e1s todo el trabajo que hayas realizado.",
    "Individual file size must be {max_files_mb}MB or less.": "Cada archivo individual debe tener {max_files_mb}MB como m\u00e1ximo.",
    "January": "Enero",
    "July": "Julio",
    "June": "Junio",
    "List of Open Assessments is unavailable": "El listado de tareas abiertas no est\u00e1 disponible",
    "March": "Marzo",
    "May": "Mayo",
    "Midnight": "Medianoche",
    "Missing required query parameter course_id": "Falta el par\u00e1metro obligatorio course_id",
    "Multiple teams returned for course": "Varios equipos han regresado por curso",
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
    "One or more rescheduling tasks failed.": "Error en una o m\u00e1s tareas de reprogramaci\u00f3n.",
    "Option Deleted": "Opci\u00f3n eliminada",
    "Paragraph": "P\u00e1rrafo",
    "Peer": "Compa\u00f1ero",
    "Peer Responses Received": "Respuestas de compa\u00f1eros recibidas",
    "Peers Assessed": "Compa\u00f1ero evaluado",
    "Please wait": "Por favor, espera",
    "Preformatted": "Preformateado",
    "Problem cloning rubric": "Problema al duplicar la r\u00fabrica",
    "Proctored exam {exam_name} in {course_name} for user {username}": "Examen supervisado {exam_name} en {course_name} para {username}",
    "Refresh": "Refrescar",
    "Remove": "Eliminar",
    "Remove all": "Eliminar todos",
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
    "Status of Your Response": "Estado de tu respuesta",
    "The \"{name}\" problem is configured to require a minimum of {min_grades} peer grades, and asks to review {min_graded} peers.": "El problema \"{name}\" est\u00e1 configurado con un m\u00ednimo de {min_grades} calificaciones de compa\u00f1eros y solicita revisar al menos a {min_graded} compa\u00f1eros.",
    "The display of ungraded and checked out responses could not be loaded.": "No se ha podido cargar la visualizaci\u00f3n de respuestas sin calificar y revisadas.",
    "The following file types are not allowed: ": "No se permiten los siguientes tipos de archivos:",
    "The maximum number files that can be saved is ": "El n\u00famero m\u00e1ximo de archivos que se pueden guardar es",
    "The server could not be contacted.": "No se ha podido contactar con el servidor.",
    "The staff assessment form could not be loaded.": "La evaluaci\u00f3n por el equipo docente no ha podido cargarse.",
    "The submission could not be removed from the grading pool.": "La entrega no ha podido eliminarse del tabl\u00f3n de calificaciones.",
    "There are currently {stuck_learners} learners in the waiting state, meaning they have not yet met all requirements for Peer Assessment. ": "Actualmente se encuentran {stuck_learners} estudiantes en estado de espera, lo cual significa que a\u00fan no cumplen con todos los requisitos para la evaluaci\u00f3n por pares.",
    "This ORA has already been released. Changes will only affect learners making new submissions. Existing submissions will not be modified by this change.": "Esta tarea de respuesta abierta ya ha sido publicada. Los cambios solo afectar\u00e1n a los estudiantes que hagan nuevas entregas. Las entregas ya realizadas no se ver\u00e1n modificadas por este cambio.",
    "This assessment could not be submitted.": "Esta tarea no ha podido enviarse.",
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
    "Today": "Hoy",
    "Tomorrow": "Ma\u00f1ana",
    "Total Responses": "Respuestas totales",
    "Training": "Pr\u00e1ctica",
    "Type into this box to filter down the list of available %s.": "Escriba en este cuadro para filtrar la lista de %s disponibles",
    "Unable to load": "No se ha podido cargar",
    "Unexpected server error.": "Error inesperado del servidor",
    "Unit Name": "Nombre de la unidad",
    "Units": "Unidades",
    "Unnamed Option": "Opci\u00f3n sin nombre",
    "User lookup failed": "Error de b\u00fasqueda de usuario",
    "Username": "Nombre de usuario",
    "View and grade responses": "Ver y calificar respuestas",
    "Waiting": "Esperando",
    "Warning": "Aviso",
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
    "error count: ": "recuento de errores:",
    "one letter Friday\u0004F": "V",
    "one letter Monday\u0004M": "L",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "J",
    "one letter Tuesday\u0004T": "M",
    "one letter Wednesday\u0004W": "M"
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

