

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
      "%(sel)s de %(cnt)s selecionado",
      "%(sel)s de %(cnt)s selecionados"
    ],
    "(required):": "(obrigat\u00f3rio):",
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "April": "Abril",
    "Assessment": "Avalia\u00e7\u00e3o",
    "Assessments": "Avalia\u00e7\u00f5es",
    "August": "Agosto",
    "Available %s": "Dispon\u00edvel %s",
    "Back to Full List": "Voltar \u00e0 lista completa",
    "Block view is unavailable": "A visualiza\u00e7\u00e3o em grelha n\u00e3o est\u00e1 dispon\u00edvel",
    "Cancel": "Cancelar",
    "Changes to steps that are not selected as part of the assignment will not be saved.": "As altera\u00e7\u00f5es \u00e0s etapas que n\u00e3o est\u00e3o selecionados como parte da tarefa, n\u00e3o ser\u00e3o guardadas.",
    "Choose": "Escolher",
    "Choose a Date": "Escolha a Data",
    "Choose a Time": "Escolha a Hora",
    "Choose a time": "Escolha a hora",
    "Choose all": "Escolher todos",
    "Chosen %s": "Escolhido %s",
    "Click to choose all %s at once.": "Clique para escolher todos os %s de uma vez.",
    "Click to remove all chosen %s at once.": "Clique para remover todos os %s escolhidos de uma vez.",
    "Could not retrieve download url.": "N\u00e3o foi poss\u00edvel obter os dados a partir do URL definido.",
    "Could not retrieve upload url.": "N\u00e3o foi poss\u00edvel recuperar o url de envio.",
    "Couldn't Save This Assignment": "N\u00e3o \u00e9 poss\u00edvel guardar esta tarefa",
    "Criterion Added": "Crit\u00e9rio Adicionado",
    "Criterion Deleted": "Crit\u00e9rio eliminado",
    "December": "Dezembro",
    "Describe ": "Descreva",
    "Do you want to upload your file before submitting?": "Deseja carregar o seu ficheiro antes de submeter?",
    "Error": "Erro",
    "Error getting the number of ungraded responses": "Erro ao obter o n\u00famero de respostas sem classifica\u00e7\u00e3o",
    "February": "Fevereiro",
    "Feedback available for selection.": "Coment\u00e1rio dispon\u00edvel para a sele\u00e7\u00e3o.",
    "File types can not be empty.": "Indique o tipo de ficheiro. ",
    "Filter": "Filtrar",
    "Final Grade Received": "Nota Final Recebida",
    "Heading 3": "T\u00edtulo 3",
    "Heading 4": "T\u00edtulo 4",
    "Heading 5": "T\u00edtulo 5",
    "Heading 6": "T\u00edtulo 6",
    "Hide": "Ocultar",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Caso saia desta p\u00e1gina sem gravar ou submeter a sua resposta, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Caso saia desta p\u00e1gina sem submeter o seu teste, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Caso saia desta p\u00e1gina sem submeter a sua auto-avalia\u00e7\u00e3o, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Caso saia desta p\u00e1gina sem submeter a sua avalia\u00e7\u00e3o individual, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "January": "Janeiro",
    "July": "Julho",
    "June": "Junho",
    "List of Open Assessments is unavailable": "Lista de Avalia\u00e7\u00f5es Abertas n\u00e3o est\u00e1 dispon\u00edvel",
    "March": "Mar\u00e7o",
    "May": "Maio",
    "Midnight": "Meia-noite",
    "Noon": "Meio-dia",
    "Not Selected": "N\u00e3o Selecionado",
    "Note: You are %s hour ahead of server time.": [
      "Nota: O seu fuso hor\u00e1rio est\u00e1 %s hora adiantado em rela\u00e7\u00e3o ao servidor.",
      "Nota: O seu fuso hor\u00e1rio est\u00e1 %s horas adiantado em rela\u00e7\u00e3o ao servidor."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: O use fuso hor\u00e1rio est\u00e1 %s hora atrasado em rela\u00e7\u00e3o ao servidor.",
      "Nota: O use fuso hor\u00e1rio est\u00e1 %s horas atrasado em rela\u00e7\u00e3o ao servidor."
    ],
    "November": "Novembro",
    "Now": "Agora",
    "October": "Outubro",
    "One or more rescheduling tasks failed.": "Ocorreu erro no reagendamento de uma ou mais tarefas.",
    "Option Deleted": "Op\u00e7\u00e3o eliminada",
    "Paragraph": "Par\u00e1grafo",
    "Peer": "Par",
    "Please correct the outlined fields.": "Por favor, corrija os campos indicados.",
    "Please wait": "Aguarde, por favor",
    "Preformatted": "Pr\u00e9-formatado",
    "Remove": "Remover",
    "Remove all": "Remover todos",
    "Saving...": "A guardar...",
    "Self": "Auto",
    "September": "Setembro",
    "Server error.": "Erro de servidor.",
    "Show": "Mostrar",
    "Staff": "Equipa",
    "Status of Your Response": "Estado da sua Resposta",
    "The display of ungraded and checked out responses could not be loaded.": "N\u00e3o foi poss\u00edvel carregar a exibi\u00e7\u00e3o de respostas entregues n\u00e3o classificadas.",
    "The following file types are not allowed: ": "Os seguintes tipos de ficheiro n\u00e3o s\u00e3o permitidos: ",
    "The server could not be contacted.": "N\u00e3o foi poss\u00edvel contactar o servidor.",
    "The staff assessment form could not be loaded.": "N\u00e3o foi poss\u00edvel carregar o formul\u00e1rio de avalia\u00e7\u00e3o da Equipa.",
    "The submission could not be removed from the grading pool.": "N\u00e3o foi poss\u00edvel remover a submiss\u00e3o da pool de classifica\u00e7\u00e3o.",
    "This assessment could not be submitted.": "N\u00e3o foi poss\u00edvel submeter esta avalia\u00e7\u00e3o.",
    "This feedback could not be submitted.": "N\u00e3o foi poss\u00edvel submeter este coment\u00e1rio.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Poder\u00e1 escolher alguns, selecionando-os na caixa abaixo e clicando na seta \"Escolher\" entre as duas caixas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta \u00e9 a lista de %s escolhidos. Poder\u00e1 remover alguns, selecionando-os na caixa abaixo e clicando na seta \"Remover\" entre as duas caixas.",
    "This problem could not be saved.": "N\u00e3o foi poss\u00edvel gravar este problema.",
    "This problem has already been released. Any changes will apply only to future assessments.": "Este problema j\u00e1 foi desbloqueado. Quaisquer altera\u00e7\u00f5es efetuadas posteriormente aplicam-se apenas a avalia\u00e7\u00f5es futuras.",
    "This response could not be saved.": "N\u00e3o foi poss\u00edvel guardar esta resposta.",
    "This response could not be submitted.": "N\u00e3o foi poss\u00edvel submeter esta resposta.",
    "This response has been saved but not submitted.": "Esta resposta foi guardada mas n\u00e3o foi submetida.",
    "This response has not been saved.": "Esta resposta n\u00e3o foi guardada.",
    "This section could not be loaded.": "N\u00e3o foi poss\u00edvel carregar esta sec\u00e7\u00e3o.",
    "Thumbnail view of ": "Visualiza\u00e7\u00e3o em miniatura de ",
    "Today": "Hoje",
    "Tomorrow": "Amanh\u00e3",
    "Total Responses": "Total de Respostas",
    "Training": "Forma\u00e7\u00e3o",
    "Type into this box to filter down the list of available %s.": "Digite nesta caixa para filtrar a lista de %s dispon\u00edveis.",
    "Unable to load": "N\u00e3o foi poss\u00edvel carregar",
    "Unexpected server error.": "Erro do servidor.",
    "Unit Name": "T\u00edtulo da Unidade",
    "Units": "Unidades",
    "Unnamed Option": "Op\u00e7\u00e3o sem t\u00edtulo",
    "Waiting": "A aguardar",
    "Warning": "Aviso",
    "Yesterday": "Ontem",
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Adicionou um novo crit\u00e9rio. Necessitar\u00e1 de selecionar uma op\u00e7\u00e3o para o crit\u00e9rio, na etapa de Forma\u00e7\u00e3o do Estudante. Para tal, clique no separador Configura\u00e7\u00f5es.",
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Eliminou um crit\u00e9rio. O crit\u00e9rio foi removido dos exemplos de resposta da etapa de Forma\u00e7\u00e3o do Estudante.",
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Eliminou todas as op\u00e7\u00f5es para este crit\u00e9rio. O crit\u00e9rio foi removido dos exemplos de resposta da etapa de Forma\u00e7\u00e3o do Estudante.",
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Eliminou uma op\u00e7\u00e3o. Esta op\u00e7\u00e3o foi removida do seu crit\u00e9rio nos exemplos de respostas da etapa Forma\u00e7\u00e3o do Estudante. Deve selecionar uma nova op\u00e7\u00e3o para esse crit\u00e9rio.",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Selecionou uma a\u00e7\u00e3o mas ainda n\u00e3o guardou as mudan\u00e7as dos campos individuais. Provavelmente querer\u00e1 o bot\u00e3o Ir ao inv\u00e9s do bot\u00e3o Guardar.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Selecionou uma a\u00e7\u00e3o mas ainda n\u00e3o guardou as mudan\u00e7as dos campos individuais. Carregue em OK para gravar. Precisar\u00e1 de correr de novo a a\u00e7\u00e3o.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tem mudan\u00e7as por guardar nos campos individuais. Se usar uma a\u00e7\u00e3o, as suas mudan\u00e7as por guardar ser\u00e3o perdidas.",
    "You must provide a learner name.": "Deve indicar o nome de um estudante.",
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Est\u00e1 prestes a submeter a sua resposta para esta tarefa. Depois de a submeter, n\u00e3o \u00e9 poss\u00edvel alter\u00e1-la ou submeter uma nova resposta.",
    "Your file ": "O seu ficheiro ",
    "one letter Friday\u0004F": "S",
    "one letter Monday\u0004M": "S",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "Q",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "Q"
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
    "DATETIME_FORMAT": "j \\d\\e F \\d\\e Y \u00e0\\s H:i",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d",
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%Y",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%d/%m/%y"
    ],
    "DATE_FORMAT": "j \\d\\e F \\d\\e Y",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%d/%m/%Y",
      "%d/%m/%y"
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

