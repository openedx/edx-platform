

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
      "%(sel)s de %(cnt)s seleccionado/a",
      "%(sel)s de %(cnt)s seleccionados/as"
    ],
    "6 a.m.": "6 AM",
    "6 p.m.": "6 PM",
    "April": "Abril",
    "August": "Agosto",
    "Available %s": "%s disponibles",
    "Cancel": "Cancelar",
    "Choose": "Seleccionar",
    "Choose a Date": "Seleccione una Fecha",
    "Choose a Time": "Seleccione una Hora",
    "Choose a time": "Elija una hora",
    "Choose all": "Seleccionar todos/as",
    "Chosen %s": "%s seleccionados/as",
    "Click to choose all %s at once.": "Haga click para seleccionar todos/as los/as %s.",
    "Click to remove all chosen %s at once.": "Haga clic para deselecionar todos/as los/as %s.",
    "December": "Diciembre",
    "February": "Febrero",
    "Filter": "Filtro",
    "Hide": "Ocultar",
    "January": "Enero",
    "July": "Julio",
    "June": "Junio",
    "March": "Marzo",
    "May": "Mayo",
    "Midnight": "Medianoche",
    "Noon": "Mediod\u00eda",
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
    "Remove": "Eliminar",
    "Remove all": "Eliminar todos/as",
    "September": "Setiembre",
    "Show": "Mostrar",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta es la lista de %s disponibles. Puede elegir algunos/as seleccion\u00e1ndolos/as en el cuadro de abajo y luego haciendo click en la flecha \"Seleccionar\" ubicada entre las dos listas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta es la lista de %s seleccionados. Puede deseleccionar algunos de ellos activ\u00e1ndolos en la lista de abajo y luego haciendo click en la flecha \"Eliminar\" ubicada entre las dos listas.",
    "Today": "Hoy",
    "Tomorrow": "Ma\u00f1ana",
    "Type into this box to filter down the list of available %s.": "Escriba en esta caja para filtrar la lista de %s disponibles.",
    "Yesterday": "Ayer",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Ha seleccionado una acci\u00f3n pero no ha realizado ninguna modificaci\u00f3n en campos individuales. Es probable que lo que necesite usar en realidad sea el bot\u00f3n Ejecutar y no el bot\u00f3n Guardar.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Ha seleccionado una acci\u00f3n, pero todav\u00eda no ha grabado las modificaciones que ha realizado en campos individuales. Por favor haga click en Aceptar para grabarlas. Necesitar\u00e1 ejecutar la acci\u00f3n nuevamente.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tiene modificaciones sin guardar en campos modificables individuales. Si ejecuta una acci\u00f3n las mismas se perder\u00e1n.",
    "one letter Friday\u0004F": "V",
    "one letter Monday\u0004M": "L",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "J",
    "one letter Tuesday\u0004T": "M",
    "one letter Wednesday\u0004W": "M"
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

