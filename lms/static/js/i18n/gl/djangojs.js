

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
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s escollido",
      "%(sel)s de %(cnt)s escollidos"
    ],
    "%s selected option not visible": [
      "%s opci\u00f3n seleccionada non visible",
      "%s opci\u00f3ns seleccionadas non visibles"
    ],
    "6 a.m.": "6 da ma\u00f1\u00e1",
    "6 p.m.": "6 da tarde",
    "April": "Abril",
    "August": "Agosto",
    "Available %s": "%s dispo\u00f1\u00edbeis",
    "Cancel": "Cancelar",
    "Choose": "Escoller",
    "Choose a Date": "Escolla unha Data",
    "Choose a Time": "Escolla unha Hora",
    "Choose a time": "Escolla unha hora",
    "Choose all": "Escoller todo",
    "Chosen %s": "%s escollido/a(s)",
    "Click to choose all %s at once.": "Prema para escoller todos/as os/as '%s' dunha vez.",
    "Click to remove all chosen %s at once.": "Faga clic para eliminar da lista todos/as os/as '%s' escollidos/as.",
    "December": "Decembro",
    "February": "Febreiro",
    "Filter": "Filtro",
    "Hide": "Esconder",
    "January": "Xaneiro",
    "July": "Xullo",
    "June": "Xu\u00f1o",
    "March": "Marzo",
    "May": "Maio",
    "Midnight": "Medianoite",
    "Noon": "Mediod\u00eda",
    "Note: You are %s hour ahead of server time.": [
      "Nota: Est\u00e1 %s hora por diante da hora do servidor.",
      "Nota: Est\u00e1 %s horas por diante da hora do servidor."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: Est\u00e1 %s hora por detr\u00e1s da hora do servidor.",
      "Nota: Est\u00e1 %s horas por detr\u00e1s da hora do servidor."
    ],
    "November": "Novembro",
    "Now": "Agora",
    "October": "Outubro",
    "Remove": "Retirar",
    "Remove all": "Retirar todos",
    "September": "Setembro",
    "Show": "Amosar",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta \u00e9 unha lista de %s dispo\u00f1\u00edbeis. Pode escoller alg\u00fans seleccion\u00e1ndoos na caixa inferior e a continuaci\u00f3n facendo clic na frecha \"Escoller\" situada entre as d\u00faas caixas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta \u00e9 a lista de %s escollidos/as. Pode eliminar alg\u00fans seleccion\u00e1ndoos na caixa inferior e a continuaci\u00f3n facendo clic na frecha \"Eliminar\" situada entre as d\u00faas caixas.",
    "Today": "Hoxe",
    "Tomorrow": "Ma\u00f1\u00e1",
    "Type into this box to filter down the list of available %s.": "Escriba nesta caixa para filtrar a lista de %s dispo\u00f1\u00edbeis.",
    "Type into this box to filter down the list of selected %s.": "Escriba nesta caixa para filtrar a lista de %s seleccionados.",
    "Yesterday": "Onte",
    "You have selected an action, and you haven\u2019t made any changes on individual fields. You\u2019re probably looking for the Go button rather than the Save button.": "Escolleu unha acci\u00f3n, pero a\u00ednda non gardou os cambios nos campos individuais. Probablemente estea buscando o bot\u00f3n Ir no canto do bot\u00f3n Gardar.",
    "You have selected an action, but you haven\u2019t saved your changes to individual fields yet. Please click OK to save. You\u2019ll need to re-run the action.": "Escolleu unha acci\u00f3n, pero a\u00ednda non gardou os cambios nos campos individuais. Prema OK para gardar. Despois ter\u00e1 que volver executar a acci\u00f3n.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tes cambios sen guardar en campos editables individuales. Se executas unha acci\u00f3n, os cambios non gardados perderanse.",
    "abbrev. month April\u0004Apr": "Abr",
    "abbrev. month August\u0004Aug": "Ago",
    "abbrev. month December\u0004Dec": "Dec",
    "abbrev. month February\u0004Feb": "Feb",
    "abbrev. month January\u0004Jan": "Xan",
    "abbrev. month July\u0004Jul": "Xul",
    "abbrev. month June\u0004Jun": "Xu\u00f1",
    "abbrev. month March\u0004Mar": "Mar",
    "abbrev. month May\u0004May": "Maio",
    "abbrev. month November\u0004Nov": "Nov",
    "abbrev. month October\u0004Oct": "Out",
    "abbrev. month September\u0004Sep": "Set",
    "one letter Friday\u0004F": "V",
    "one letter Monday\u0004M": "L",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "X",
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
    "DATETIME_FORMAT": "j \\d\\e F \\d\\e Y \\\u00e1\\s H:i",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%m/%d/%Y %H:%M:%S",
      "%m/%d/%Y %H:%M:%S.%f",
      "%m/%d/%Y %H:%M",
      "%m/%d/%y %H:%M:%S",
      "%m/%d/%y %H:%M:%S.%f",
      "%m/%d/%y %H:%M"
    ],
    "DATE_FORMAT": "j \\d\\e F \\d\\e Y",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%m/%d/%Y",
      "%m/%d/%y",
      "%b %d %Y",
      "%b %d, %Y",
      "%d %b %Y",
      "%d %b, %Y",
      "%B %d %Y",
      "%B %d, %Y",
      "%d %B %Y",
      "%d %B, %Y"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j \\d\\e F",
    "NUMBER_GROUPING": 0,
    "SHORT_DATETIME_FORMAT": "d-m-Y, H:i",
    "SHORT_DATE_FORMAT": "d-m-Y",
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

