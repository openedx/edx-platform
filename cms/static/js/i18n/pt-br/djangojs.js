

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
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s selecionado", 
      "%(sel)s de %(cnt)s selecionados"
    ], 
    "6 a.m.": "6 da manh\u00e3", 
    "6 p.m.": "6 da tarde", 
    "Add a clear and descriptive title to encourage participation. (Required)": "Adicione um t\u00eetulo claro e descritivo para encorajar a participa\u00e7\u00e3o dos outros colegas.(Obrigat\u00f3rio)", 
    "April": "Abril", 
    "August": "Agosto", 
    "Available %s": "%s dispon\u00edveis", 
    "Bookmark this page": "Favoritar esta p\u00e1gina", 
    "Bookmarked": "Salvo nos Favoritos", 
    "Bookmarked on": "Salvo nos Favoritos em", 
    "Cancel": "Cancelar", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Altera\u00e7\u00f5es nos passos que n\u00e3o forem selecionados como parte da tarefa n\u00e3o ser\u00e3o salvas.", 
    "Choose": "Escolher", 
    "Choose a Date": "Escolha uma data", 
    "Choose a Time": "Escolha um hor\u00e1rio", 
    "Choose a time": "Escolha uma hora", 
    "Choose all": "Escolher todos", 
    "Chosen %s": "%s escolhido(s)", 
    "Click to choose all %s at once.": "Clique para escolher todos os %s de uma s\u00f3 vez", 
    "Click to remove all chosen %s at once.": "Clique para remover de uma s\u00f3 vez todos os %s escolhidos.", 
    "Could not retrieve download url.": "N\u00e3o foi poss\u00edvel recuperar o url de download.", 
    "Could not retrieve upload url.": "N\u00e3o foi poss\u00edvel recuperar o url de upload.", 
    "Couldn't Save This Assignment": "N\u00e3o Foi Poss\u00edvel Salvar Esta Tarefa", 
    "Criterion Added": "Crit\u00e9rio Adicionado", 
    "Criterion Deleted": "Crit\u00e9rio Apagado", 
    "December": "Dezembro", 
    "Do you want to upload your file before submitting?": "Voc\u00ea deseja fazer upload de seu arquivo antes de enviar?", 
    "Error": "Erro", 
    "Error getting the number of ungraded responses": "Erro ao obter o n\u00famero de respostas n\u00e3o corrigidas.", 
    "February": "Fevereiro", 
    "File type is not allowed.": "Tipo de arquivo n\u00e3o permitido.", 
    "File types can not be empty.": "Tipo de arquivo n\u00e3o pode estar vazio.", 
    "Filter": "Filtro", 
    "Go to Dashboard": "Ir para a Painel de controle", 
    "Go to my Dashboard": "Ir para o meu Painel de controle", 
    "Go to your Dashboard": "Ir para o seu Painel de controle", 
    "Hide": "Esconder", 
    "Hide Discussion": "Ocultar discuss\u00e3o", 
    "If you don't verify your identity now, you can still explore your course from your dashboard. You will receive periodic reminders from %(platformName)s to verify your identity.": "Se voc\u00ea n\u00e3o confirmar a sua identidade agora, voc\u00ea ainda poder\u00e1 explorar o curso pelo seu painel de controle. Voc\u00ea vai receber lembretes peri\u00f3dicos de %(platformName)s para verificar a sua identidade.", 
    "If you don't verify your identity now, you can still explore your course from your dashboard. You will receive periodic reminders from {platformName} to verify your identity.": "Se voc\u00ea n\u00e3o confirmar a sua identidade agora, voc\u00ea ainda poder\u00e1 explorar o curso pelo seu painel de controle. Voc\u00ea vai receber lembretes peri\u00f3dicos de {platformName} para verificar a sua identidade.", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Se voc\u00ea deixar esta p\u00e1gina sem salvar ou enviar a sua resposta, voc\u00ea perder\u00e1 qualquer trabalho que tenha realizado.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Se voc\u00ea deixar esta p\u00e1gina sem salvar a sua avalia\u00e7\u00e3o pelos pares, voc\u00ea perder\u00e1 qualquer trabalho que tenha realizado.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Se voc\u00ea deixar esta p\u00e1gina sem enviar a sua auto-avalia\u00e7\u00e3o, voc\u00ea perder\u00e1 qualquer trabalho que tenha realizado.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Se voc\u00ea deixar esta p\u00e1gina sem enviar a sua avalia\u00e7\u00e3o de equipe, voc\u00ea vai perder qualquer trabalho que tenha realizado.", 
    "January": "Janeiro", 
    "July": "Julho", 
    "June": "Junho", 
    "March": "Mar\u00e7o", 
    "May": "Maio", 
    "Midnight": "Meia-noite", 
    "Noon": "Meio-dia", 
    "Not Selected": "N\u00e3o selecionado", 
    "Note: You are %s hour ahead of server time.": [
      "Nota: Voc\u00ea est\u00e1 %s hora \u00e0 frente do hor\u00e1rio do servidor.", 
      "Nota: Voc\u00ea est\u00e1 %s horas \u00e0 frente do hor\u00e1rio do servidor."
    ], 
    "Note: You are %s hour behind server time.": [
      "Nota: Voc\u00ea est\u00e1 %s hora atr\u00e1s do tempo do servidor.", 
      "Nota: Voc\u00ea est\u00e1 %s horas atr\u00e1s do hor\u00e1rio do servidor."
    ], 
    "November": "Novembro", 
    "Now": "Agora", 
    "October": "Outubro", 
    "One or more rescheduling tasks failed.": "Uma ou mais tarefas de reagendamento falharam.", 
    "Option Deleted": "Op\u00e7\u00e3o Apagada", 
    "Please correct the outlined fields.": "Por favor, corrija os campos destacados.", 
    "Questions raise issues that need answers. Discussions share ideas and start conversations. (Required)": "Perguntas levantam quest\u00f5es que precisam de respostas. Discuss\u00f5es compartilham ideias e iniciam conversas. (Obrigat\u00f3rio)", 
    "Remove": "Remover", 
    "Remove all": "Remover todos", 
    "Return to Your Dashboard": "Retornar ao painel de controle", 
    "Saving...": "Salvando...", 
    "September": "Setembro", 
    "Show": "Mostrar", 
    "Show Discussion": "Exibir discuss\u00e3o", 
    "Status of Your Response": "Situa\u00e7\u00e3o da Sua Resposta", 
    "The display of ungraded and checked out responses could not be loaded.": "N\u00e3o foi poss\u00edvel carregar a exibi\u00e7\u00e3o de respostas corrigidas e n\u00e3o corrigidas. ", 
    "The following file types are not allowed: ": "Os seguintes tipos de arquivos n\u00e3o s\u00e3o permitidos:", 
    "The server could not be contacted.": "N\u00e3o foi poss\u00edvel contactar o servidor.", 
    "The staff assessment form could not be loaded.": "N\u00e3o foi poss\u00edvel carregar o formul\u00e1rio de avalia\u00e7\u00e3o pessoal.", 
    "The submission could not be removed from the grading pool.": "A tarefa enviada n\u00e3o p\u00f4de ser removida da lista para avalia\u00e7\u00e3o.", 
    "This assessment could not be submitted.": "Esta avalia\u00e7\u00e3o n\u00e3o p\u00f4de ser submetida.", 
    "This feedback could not be submitted.": "Este feedback n\u00e3o p\u00f4de ser enviado.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Voc\u00ea pode escolh\u00ea-los(as) selecionando-os(as) abaixo e clicando na seta \"Escolher\" entre as duas caixas.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Voc\u00ea pode remov\u00ea-los(as) selecionando-os(as) abaixo e clicando na seta \"Remover\" entre as duas caixas.", 
    "This problem could not be saved.": "Este problema n\u00e3o p\u00f4de ser salvo.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "A solu\u00e7\u00e3o deste problema j\u00e1 foi colocada no software. Quaisquer altera\u00e7\u00f5es ser\u00e3o aplicadas apenas em avalia\u00e7\u00f5es futuras.", 
    "This response could not be saved.": "Esta resposta n\u00e3o p\u00f4de ser salva.", 
    "This response could not be submitted.": "Esta resposta n\u00e3o p\u00f4de ser enviada", 
    "This response has been saved but not submitted.": "Esta resposta foi salva mas n\u00e3o foi enviada.", 
    "This response has not been saved.": "Esta resposta n\u00e3o foi salva.", 
    "This section could not be loaded.": "Esta se\u00e7\u00e3o n\u00e3o p\u00f4de ser carregada.", 
    "Today": "Hoje", 
    "Tomorrow": "Amanh\u00e3", 
    "Type into this box to filter down the list of available %s.": "Digite nessa caixa para filtrar a lista de %s dispon\u00edveis.", 
    "Unable to load": "N\u00e3o foi poss\u00edvel carregar", 
    "Unexpected server error.": "Ocorreu um erro de servidor inesperado.", 
    "Unnamed Option": "Op\u00e7\u00e3o Sem Nome", 
    "Use bookmarks to help you easily return to courseware pages. To bookmark a page, click \"Bookmark this page\" under the page title.": "Use os favoritos para ajud\u00e1-lo a facilmente retornar para as p\u00e1ginas do material do curso. Para adicionar uma p\u00e1gina aos favoritos clique em \"Favoritar esta p\u00e1gina\" abaixo do t\u00edtulo da p\u00e1gina.", 
    "Warning": "Aviso", 
    "We have received your information and are verifying your identity. You will see a message on your dashboard when the verification process is complete (usually within 1-2 days). In the meantime, you can still access all available course content.": "Recebemos as suas informa\u00e7\u00f5es e estamos verificando a sua identifica\u00e7\u00e3o. Voc\u00ea receber\u00e1 uma mensagem em seu painel de controle quando o processo de verifica\u00e7\u00e3o estiver conclu\u00eddo (normalmente entre 1-2 dias). Enquanto isso, voc\u00ea ainda pode acessar a todo o conte\u00fado do curso.", 
    "Yesterday": "Ontem", 
    "You can upload files with these file types: ": "Voc\u00ea pode fazer upload de arquivos com esses formatos:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Voc\u00ea adicionou um crit\u00e9rio. Voc\u00ea precisa selecionar uma op\u00e7\u00e3o para o crit\u00e9rio na etapa de Treinamento do Estudante. Para fazer isso, clique na guia Configura\u00e7\u00f5es.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Voc\u00ea excluiu um crit\u00e9rio. O crit\u00e9rio foi removido do exemplo de respostas na etapa de Treinamento do Estudante.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Voc\u00ea excluiu todas as op\u00e7\u00f5es para este crit\u00e9rio. O crit\u00e9rio foi removido a partir das respostas de amostra na etapa de Treinamento do Estudante.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Voc\u00ea excluiu uma op\u00e7\u00e3o. Essa op\u00e7\u00e3o foi removida deste crit\u00e9rio nas respostas de exemplo na etapa Treinamento do Estudante. Voc\u00ea pode ter que selecionar uma nova op\u00e7\u00e3o para o crit\u00e9rio.", 
    "You have not bookmarked any courseware pages yet": "Voc\u00ea n\u00e3o salvou nenhuma p\u00e1gina do curso em seus Favoritos at\u00e9 o momento.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Voc\u00ea selecionou uma a\u00e7\u00e3o, e voc\u00ea n\u00e3o fez altera\u00e7\u00f5es em campos individuais. Voc\u00ea provavelmente est\u00e1 procurando o bot\u00e3o Ir ao inv\u00e9s do bot\u00e3o Salvar.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Voc\u00ea selecionou uma a\u00e7\u00e3o, mas voc\u00ea n\u00e3o salvou as altera\u00e7\u00f5es de cada campo ainda. Clique em OK para salvar. Voc\u00ea vai precisar executar novamente a a\u00e7\u00e3o.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Voc\u00ea tem altera\u00e7\u00f5es n\u00e3o salvas em campos edit\u00e1veis individuais. Se voc\u00ea executar uma a\u00e7\u00e3o suas altera\u00e7\u00f5es n\u00e3o salvas ser\u00e3o perdidas.", 
    "You must provide a learner name.": "Voc\u00ea deve fornecer o nome do aluno.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Voc\u00ea est\u00e1 prestes a enviar sua resposta para este trabalho. Depois que sua resposta for enviada voc\u00ea n\u00e3o poder\u00e1 mud\u00e1-la ou enviar uma nova resposta.", 
    "Your question or idea (required)": "Sua pergunta ou opini\u00e3o (obrigat\u00f3rio)", 
    "answered question": "pergunta respondida", 
    "one letter Friday\u0004F": "S", 
    "one letter Monday\u0004M": "S", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "D", 
    "one letter Thursday\u0004T": "Q", 
    "one letter Tuesday\u0004T": "T", 
    "one letter Wednesday\u0004W": "Q", 
    "question posted %(time_ago)s by %(author)s": "pergunta postada %(time_ago)s por %(author)s", 
    "unanswered question": "pergunta n\u00e3o respondida"
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
    "DATETIME_FORMAT": "j \\d\\e F \\d\\e Y \u00e0\\s H:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S", 
      "%d/%m/%Y %H:%M:%S.%f", 
      "%d/%m/%Y %H:%M", 
      "%d/%m/%Y", 
      "%d/%m/%y %H:%M:%S", 
      "%d/%m/%y %H:%M:%S.%f", 
      "%d/%m/%y %H:%M", 
      "%d/%m/%y", 
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
    "FIRST_DAY_OF_WEEK": "0", 
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

