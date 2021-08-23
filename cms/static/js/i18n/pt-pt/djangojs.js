

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
    "\n                    Make sure you are on a computer with a webcam, and that you have valid photo identification\n                    such as a driver's license or passport, before you continue.\n                ": "\n                    Certifique-se que est\u00e1 num computador com uma webcam, e que tem identifica\u00e7\u00e3o fotogr\u00e1fica v\u00e1lida\n                    como uma carta de condu\u00e7\u00e3o ou passaporte, antes de continuar.\n                ",
    "\n                    Your verification attempt failed. Please read our guidelines to make\n                    sure you understand the requirements for successfully completing verification,\n                    then try again.\n                ": "\n                    A sua tentativa de verifica\u00e7\u00e3o falhou. Por favor, leia as nossas directrizes para se\n                    certificar de que compreende os requisitos para concluir com \u00eaxito a verifica\u00e7\u00e3o,,\n                    depois tente novamente.\n                ",
    "\n                    Your verification has expired. You must successfully complete a new identity verification\n                    before you can start the proctored exam.\n                ": "\n                    A sua verifica\u00e7\u00e3o expirou. Deve concluir com \u00eaxito uma nova verifica\u00e7\u00e3o de identidade\n                    antes de poder iniciar o exame supervisionado.\n                ",
    "\n                    Your verification is pending. Results should be available 2-3 days after you\n                    submit your verification.\n                ": "\n                    A sua verifica\u00e7\u00e3o est\u00e1 pendente. Os resultados devem estar dispon\u00edveis 2-3 dias depois de\n                    submeter a sua verifica\u00e7\u00e3o.\n                ",
    "\n                Complete your verification before starting the proctored exam.\n            ": "\n                Complete a sua verifica\u00e7\u00e3o antes de iniciar o exame supervisionado.\n            ",
    "\n                You must successfully complete identity verification before you can start the proctored exam.\n            ": "\n                Voc\u00ea deve concluir com \u00eaxito a verifica\u00e7\u00e3o de identidade antes de poder iniciar o exame supervisionado.\n            ",
    "\n            Do not close this window before you finish your exam. if you close this window, your proctoring session ends, and you will not successfully complete the proctored exam.\n          ": "\n            N\u00e3o feche esta janela antes de terminar o seu exame. se fechar esta janela, a sua sess\u00e3o de supervis\u00e3o termina, e n\u00e3o concluir\u00e1 com sucesso o exame supervisionado.\n          ",
    "\n            Return to the %(platform_name)s course window to start your exam. When you have finished your exam and\n            have marked it as complete, you can close this window to end the proctoring session\n            and upload your proctoring session data for review.\n          ": "\n            Volte \u00e0 janela do curso %(platform_name)s course window to start your exam. para iniciar o exame. Quando terminar o exame e \n            o marcar como completo, pode fechar esta janela para encerrar a sess\u00e3o de supervis\u00e3o\n            e carregar seus dados de sess\u00e3o de supervis\u00e3o para revis\u00e3o.\n          ",
    "\n        About Proctored Exams\n        ": "\n        Sobre os Exames Supervisionados\n        ",
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n        Tem certeza que quer fazer este exame sem supervis\u00e3o?\n      ",
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\n        Por n\u00e3o reunir os pr\u00e9-requisitos necess\u00e1rios, apenas pode realizar este exame sem supervis\u00e3o.\n      ",
    "\n        Hello %(username)s,\n    ": "\n        Ol\u00e1 %(username)s,\n    ",
    "\n        I am ready to start this timed exam.\n      ": "\n       Estou pronto para come\u00e7ar este exame cronometrado.\n      ",
    "\n        No, I want to continue working.\n      ": "\n        N\u00e3o, quero continuar a trabalhar.\n      ",
    "\n        No, I'd like to continue working\n      ": "\n        N\u00e3o, eu gostaria de continuar a trabalhar.\n      ",
    "\n        The result will be visible after <strong id=\"wait_deadline\"> Loading... </strong>\n    ": "\n        O resultado ficar\u00e1 vis\u00edvel ap\u00f3s <strong id=\"wait_deadline\"> Carregando... </strong>\n    ",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was reviewed and you\n        met all proctoring requirements.\n    ": "\n        O seu exame supervisionado \"%(exam_name)s\" em\n        <a href=\"%(course_url)s\">%(course_name)s</a> foi revisto e voc\u00ea\n        satisfez todos os requisitos de supervis\u00e3o.\n    ",
    "\n        Your proctored exam \"%(exam_name)s\" in\n        <a href=\"%(course_url)s\">%(course_name)s</a> was submitted\n        successfully and will now be reviewed to ensure all exam\n        rules were followed. You should receive an email with your exam\n        status within 5 business days.\n    ": "\n        O seu exame supervisionado \"%(exam_name)s\" em\n        <a href=\"%(course_url)s\">%(course_name)s</a> foi submetido\n        com sucesso e ser\u00e1 agora revisto para assegurar todos os exames\nas regras foram seguidas. Dever\u00e1 receber um e-mail com o seu exame\n        estado dentro de 5 dias \u00fateis.\n    ",
    "\n      After you submit your exam, your exam will be graded.\n    ": "\nDepois de submeter o seu exame, o seu exame ser\u00e1 classificado.",
    "\n      Are you sure that you want to submit your timed exam?\n    ": "\n      Tem a certeza de que deseja submeter o seu exame cronometrado?\n    ",
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      Tem certeza que quer terminar o seu exame supervisionado?\n    ",
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\n      Porque a data limite j\u00e1 passou, j\u00e1 n\u00e3o pode fazer este exame.\n    ",
    "\n      Error with proctored exam\n    ": "\n      Erro com o exame supervisionado\n    ",
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\n      Se tiver alguma incapacidade,\n      poder\u00e1 ser eleg\u00edvel para uma extens\u00e3o do tempo de realiza\u00e7\u00e3o de um exame cronometrado.\n      Questione a sua equipa do curso para mais informa\u00e7\u00e3o acerca das permiss\u00f5es para obter tempo extra.\n  ",
    "\n      If you have questions about the status of your proctored exam results, contact %(platform_name)s Support.\n    ": "\n      Se tiver d\u00favidas sobre o estado dos resultados do exame supervisionado, entre em contato com o  %(platform_name)s Suporte.\n    ",
    "\n      Make sure that you have selected \"Submit\" for each problem before you submit your exam.\n    ": "\nCertifique-se de que seleccionou \"submeter\" para cada problema antes de submeter o exame.",
    "\n      The due date for this exam has passed\n    ": "\n      A data limite deste exame j\u00e1 passou\n    ",
    "\n      This exam is proctored\n    ": "\n      Este exame \u00e9 supervisionado\n    ",
    "\n      To view your exam questions and responses, select <strong>View my exam</strong>. The exam's review status is shown in the left navigation pane.\n    ": "\n      Para ver suas perguntas e respostas do exame, seleccione <strong>Ver o meu exame</strong>. O estado de revis\u00e3o do exame \u00e9 mostrado no painel de navega\u00e7\u00e3o esquerdo\n    ",
    "\n      Yes, submit my timed exam.\n    ": "\n      Sim, submeter o meu exame cronometrado.\n    ",
    "\n      You have submitted this proctored exam for review\n    ": "\n      Voc\u00ea submeteu este exame supervisionado para revis\u00e3o\n    ",
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\n      Resultado da sess\u00e3o de supervis\u00e3o: <b class=\"failure\"> N\u00e3o Satisfat\u00f3rio </b>\n    ",
    "\n    %(exam_name)s is a Timed Exam (%(total_time)s)\n    ": "\n    %(exam_name)s \u00e9 um Exame Cronometrado (%(total_time)s)\n    ",
    "\n    If you have any questions about your results, you can reach out at \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ": "\n    Se tiver alguma d\u00favida sobre os seus resultados, pode contactar  \n        <a href=\"%(contact_url)s\">\n            %(contact_url_text)s\n        </a>.\n    ",
    "\n    The following prerequisites are in a <strong>pending</strong> state and must be successfully completed before you can proceed:\n    ": "\nOs seguintes pr\u00e9-requisitos est\u00e3o num estado <strong>pendente</strong> e devem ser conclu\u00eddos com sucesso antes de prosseguir:\n  ",
    "\n    You did not satisfy the following prerequisites:\n    ": "\n    N\u00e3o re\u00fane os seguintes pr\u00e9-requisitos:\n    ",
    " From this point in time, you must follow the <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">online proctoring rules</a> to pass the proctoring review for your exam. ": " A partir deste momento, deve seguir o <a href=\"%(link_urls.online_proctoring_rules)s\" target=\"_blank\">regras de supervisi\u00e3o online</a> para passar na revis\u00e3o de supervis\u00e3o para o seu exame.   ",
    " Your Proctoring Session Has Started ": "A Sua Sess\u00e3o De Supervis\u00e3o J\u00e1 Come\u00e7ou",
    " and {num_of_minutes} minute": "e {num_of_minutes} minute",
    " and {num_of_minutes} minutes": "e {num_of_minutes} minutos",
    " to complete and submit the exam.": "para completar e submeter o exame.",
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s selecionado",
      "%(sel)s de %(cnt)s selecionados"
    ],
    "(required):": "(obrigat\u00f3rio):",
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "Additional Time (minutes)": "Tempo Adicional (minutos)",
    "After you select ": "Depois de selecionar",
    "All Unreviewed": "Todos Por Rever",
    "All Unreviewed Failures": "Todas as Falhas n\u00e3o Revistas",
    "April": "Abril",
    "Are you sure you want to delete the following file? It cannot be restored.\nFile: ": "Tem certeza de que deseja apagar o seguinte ficheiro? N\u00e3o pode ser restaurado.\nFicheiro: ",
    "Assessment": "Avalia\u00e7\u00e3o",
    "Assessments": "Avalia\u00e7\u00f5es",
    "August": "Agosto",
    "Available %s": "Dispon\u00edvel %s",
    "Back to Full List": "Voltar \u00e0 lista completa",
    "Block view is unavailable": "A visualiza\u00e7\u00e3o em grelha n\u00e3o est\u00e1 dispon\u00edvel",
    "Can I request additional time to complete my exam?": "Posso pedir mais tempo para completar o meu exame?",
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
    "Close": "Fechar",
    "Continue Exam Without Proctoring": "Continuar o Exame Sem Supervis\u00e3o",
    "Continue to Verification": "Continuar a Verifica\u00e7\u00e3o",
    "Continue to my practice exam": "Continue para o meu exame de pr\u00e1tica",
    "Could not load teams information.": "N\u00e3o foi poss\u00edvel carregar informa\u00e7\u00e3o das equipas.",
    "Could not retrieve download url.": "N\u00e3o foi poss\u00edvel obter os dados a partir do URL definido.",
    "Could not retrieve upload url.": "N\u00e3o foi poss\u00edvel recuperar o url de envio.",
    "Course Id": "ID do Curso",
    "Created": "Criado",
    "Criterion Added": "Crit\u00e9rio Adicionado",
    "Criterion Deleted": "Crit\u00e9rio eliminado",
    "December": "Dezembro",
    "Declined": "Recusado",
    "Describe ": "Descreva ",
    "Download Software Clicked": "Descarregar Software Seleccionado",
    "End My Exam": "Terminar o Meu Exame",
    "Error": "Erro",
    "Error getting the number of ungraded responses": "Erro ao obter o n\u00famero de respostas sem classifica\u00e7\u00e3o",
    "Error when looking up username": "Erro ao procurar o nome de utilizador",
    "Failed Proctoring": "Supervis\u00e3o Falhou",
    "February": "Fevereiro",
    "Feedback available for selection.": "Coment\u00e1rio dispon\u00edvel para a sele\u00e7\u00e3o.",
    "File types can not be empty.": "O tipo de ficheiro n\u00e3o pode estar vazio.",
    "File upload failed: unsupported file type. Only the supported file types can be uploaded. If you have questions, please reach out to the course team.": "Falha no carregamento do ficheiro: tipo de ficheiro n\u00e3o suportado. Apenas os tipos de ficheiros suportados podem ser carregados. Se tiver d\u00favidas, entre em contato com a equipa de curso.",
    "Filter": "Filtrar",
    "Final Grade Received": "Nota Final Recebida",
    "Go Back": "Voltar Atr\u00e1s",
    "Heading 3": "T\u00edtulo 3",
    "Heading 4": "T\u00edtulo 4",
    "Heading 5": "T\u00edtulo 5",
    "Heading 6": "T\u00edtulo 6",
    "Hide": "Ocultar",
    "I am ready to start this timed exam,": "Estou pronto para come\u00e7ar este exame cronometrado,",
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Caso saia desta p\u00e1gina sem gravar ou submeter a sua resposta, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Caso saia desta p\u00e1gina sem submeter o seu teste, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Caso saia desta p\u00e1gina sem submeter a sua auto-avalia\u00e7\u00e3o, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Caso saia desta p\u00e1gina sem submeter a sua avalia\u00e7\u00e3o individual, ir\u00e1 perder todo o trabalho at\u00e9 aqui realizado.",
    "Individual file size must be {max_files_mb}MB or less.": "O tamanho do ficheiro individual deve ser {max_files_mb}MB ou menos.",
    "Is Sample Attempt": "\u00c9 Tentativa de Demonstra\u00e7\u00e3o",
    "January": "Janeiro",
    "July": "Julho",
    "June": "Junho",
    "List of Open Assessments is unavailable": "Lista de Avalia\u00e7\u00f5es Abertas n\u00e3o est\u00e1 dispon\u00edvel",
    "March": "Mar\u00e7o",
    "May": "Maio",
    "Midnight": "Meia-noite",
    "Multiple teams returned for course": "V\u00e1rias equipas voltaram para o curso",
    "Must be a Staff User to Perform this request.": "Deve ser um Utilizador da Equipa para Realizar este pedido.",
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
    "Onboarding Expired": "Integra\u00e7\u00e3o Expirada",
    "Onboarding Failed": "Integra\u00e7\u00e3o Falhou",
    "Onboarding Missing": "Integra\u00e7\u00e3o em Falta",
    "Onboarding Pending": "Integra\u00e7\u00e3o Pendente",
    "Onboarding status question": "Pergunta do estado de integra\u00e7\u00e3o",
    "One or more rescheduling tasks failed.": "Ocorreu erro no reagendamento de uma ou mais tarefas.",
    "Only ": "Apenas ",
    "Option Deleted": "Op\u00e7\u00e3o eliminada",
    "Paragraph": "Par\u00e1grafo",
    "Passed Proctoring": "Supervis\u00e3o Aprovada",
    "Peer": "Par",
    "Pending Session Review": "Revis\u00e3o de Sess\u00e3o Pendente",
    "Please wait": "Aguarde, por favor",
    "Practice Exam Completed": "Exame de pr\u00e1tica conclu\u00eddo",
    "Practice Exam Failed": "Exame de pr\u00e1tica falhou",
    "Preformatted": "Pr\u00e9-formatado",
    "Proctored Option Available": "Op\u00e7\u00e3o de Supervis\u00e3o Dispon\u00edvel",
    "Proctored Option No Longer Available": "Op\u00e7\u00e3o Supervis\u00e3o J\u00e1 N\u00e3o Est\u00e1 Dispon\u00edvel",
    "Proctored exam {exam_name} in {course_name} for user {username}": "Exame Supervisionado {exam_name} em {course_name} para o utilizador {username}",
    "Proctoring Results For {course_name} {exam_name}": "Resultados de Supervis\u00e3o Para {course_name} {exam_name}",
    "Proctoring Review In Progress For {course_name} {exam_name}": "Revis\u00e3o de Supervis\u00e3o em Curso Para {course_name} {exam_name}",
    "Ready To Resume": "Pronto Para Retomar",
    "Ready To Start": "Pronto Para Come\u00e7ar",
    "Ready To Submit": "Pronto Para Submeter",
    "Rejected": "N\u00e3o aprovado",
    "Remove": "Remover",
    "Remove all": "Remover todos",
    "Retry Verification": "Repita a verifica\u00e7\u00e3o",
    "Review Policy Exception": "Excep\u00e7\u00e3o \u00e0 Pol\u00edtica de Revis\u00e3o",
    "Saving...": "A guardar...",
    "Second Review Required": "Segunda Revis\u00e3o Obrigat\u00f3ria",
    "Self": "Auto",
    "September": "Setembro",
    "Server error.": "Erro de servidor.",
    "Show": "Mostrar",
    "Staff": "Equipa",
    "Start System Check": "Iniciar Verifica\u00e7\u00e3o do Sistema",
    "Started": "Iniciado",
    "Status of Your Response": "Estado da sua Resposta",
    "Submitted": "Submetido",
    "Take this exam without proctoring.": "Fa\u00e7a este exame sem supervis\u00e3o.",
    "Taking As Open Exam": "Fazer Como Exame Aberto",
    "Taking As Proctored Exam": "Fazer Como Exame Supervisionado",
    "Taking as Proctored": "Ministrado como Supervisionado",
    "The display of ungraded and checked out responses could not be loaded.": "N\u00e3o foi poss\u00edvel carregar a exibi\u00e7\u00e3o de respostas entregues n\u00e3o classificadas.",
    "The following file types are not allowed: ": "Os seguintes tipos de ficheiro n\u00e3o s\u00e3o permitidos: ",
    "The server could not be contacted.": "N\u00e3o foi poss\u00edvel contactar o servidor.",
    "The staff assessment form could not be loaded.": "N\u00e3o foi poss\u00edvel carregar o formul\u00e1rio de avalia\u00e7\u00e3o da Equipa.",
    "The submission could not be removed from the grading pool.": "N\u00e3o foi poss\u00edvel remover a submiss\u00e3o da pool de classifica\u00e7\u00e3o.",
    "There is no onboarding exam related to this course id.": "N\u00e3o existe nenhum exame de integra\u00e7\u00e3o relacionado com este id de curso.",
    "This assessment could not be submitted.": "N\u00e3o foi poss\u00edvel submeter esta avalia\u00e7\u00e3o.",
    "This exam has a time limit associated with it.": "Este exame tem um limite de tempo associado a ele.",
    "This feedback could not be submitted.": "N\u00e3o foi poss\u00edvel submeter este coment\u00e1rio.",
    "This grade will be applied to all members of the team. Do you want to continue?": "Esta nota ser\u00e1 aplicada a todos os membros da equipa. Quer continuar?",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Poder\u00e1 escolher alguns, selecionando-os na caixa abaixo e clicando na seta \"Escolher\" entre as duas caixas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta \u00e9 a lista de %s escolhidos. Poder\u00e1 remover alguns, selecionando-os na caixa abaixo e clicando na seta \"Remover\" entre as duas caixas.",
    "This problem could not be saved.": "N\u00e3o foi poss\u00edvel gravar este problema.",
    "This response could not be saved.": "N\u00e3o foi poss\u00edvel guardar esta resposta.",
    "This response could not be submitted.": "N\u00e3o foi poss\u00edvel submeter esta resposta.",
    "This response has been saved but not submitted.": "Esta resposta foi guardada mas n\u00e3o foi submetida.",
    "This response has not been saved.": "Esta resposta n\u00e3o foi guardada.",
    "This section could not be loaded.": "N\u00e3o foi poss\u00edvel carregar esta sec\u00e7\u00e3o.",
    "Thumbnail view of ": "Visualiza\u00e7\u00e3o em miniatura de ",
    "Timed Exam": "Exame cronometrado",
    "Timed Out": "Expirado",
    "To pass this exam, you must complete the problems in the time allowed.": "Para passar neste exame, deve completar os problemas no tempo concedido.",
    "Today": "Hoje",
    "Tomorrow": "Amanh\u00e3",
    "Total Responses": "Total de Respostas",
    "Training": "Forma\u00e7\u00e3o",
    "Type into this box to filter down the list of available %s.": "Digite nesta caixa para filtrar a lista de %s dispon\u00edveis.",
    "Unable to load": "N\u00e3o foi poss\u00edvel carregar",
    "Unexpected server error.": "Erro do servidor.",
    "Ungraded Practice Exam": "Exame Pr\u00e1tico Sem Classifica\u00e7\u00e3o",
    "Unit Name": "T\u00edtulo da Unidade",
    "Units": "Unidades",
    "Unnamed Option": "Op\u00e7\u00e3o sem t\u00edtulo",
    "User lookup failed": "A procura do utilizador falhou",
    "Verified": "Validado",
    "View my exam": "Ver o meu exame",
    "Waiting": "A aguardar",
    "Warning": "Aviso",
    "Yesterday": "Ontem",
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Eliminou um crit\u00e9rio. O crit\u00e9rio foi removido dos exemplos de resposta da etapa de Forma\u00e7\u00e3o do Estudante.",
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Eliminou todas as op\u00e7\u00f5es para este crit\u00e9rio. O crit\u00e9rio foi removido dos exemplos de resposta da etapa de Forma\u00e7\u00e3o do Estudante.",
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Eliminou uma op\u00e7\u00e3o. Esta op\u00e7\u00e3o foi removida do seu crit\u00e9rio nos exemplos de respostas da etapa Forma\u00e7\u00e3o do Estudante. Deve selecionar uma nova op\u00e7\u00e3o para esse crit\u00e9rio.",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Selecionou uma a\u00e7\u00e3o mas ainda n\u00e3o guardou as mudan\u00e7as dos campos individuais. Provavelmente querer\u00e1 o bot\u00e3o Ir ao inv\u00e9s do bot\u00e3o Guardar.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Selecionou uma a\u00e7\u00e3o mas ainda n\u00e3o guardou as mudan\u00e7as dos campos individuais. Carregue em OK para gravar. Precisar\u00e1 de correr de novo a a\u00e7\u00e3o.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tem mudan\u00e7as por guardar nos campos individuais. Se usar uma a\u00e7\u00e3o, as suas mudan\u00e7as por guardar ser\u00e3o perdidas.",
    "You must provide a learner name.": "Deve indicar o nome de um estudante.",
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Est\u00e1 prestes a submeter a sua resposta para esta tarefa. Depois de a submeter, n\u00e3o \u00e9 poss\u00edvel alter\u00e1-la ou submeter uma nova resposta.",
    "Your file ": "O seu ficheiro ",
    "a practice exam": "um exame pr\u00e1tico",
    "a proctored exam": "um exame supervisionado",
    "a timed exam": "um exame cronometrado",
    "active proctored exams": "exames supervisionados ativos",
    "an onboarding exam": "um exame de integra\u00e7\u00e3o",
    "could not determine the course_id": "N\u00e3o foi poss\u00edvel determinar o course_id",
    "courses with active proctored exams": "cursos com exames supervisionados ativos",
    "internally reviewed": "revisto internamente",
    "one letter Friday\u0004F": "S",
    "one letter Monday\u0004M": "S",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "Q",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "Q",
    "you have less than a minute remaining": "tem menos de um minuto restante",
    "you have {remaining_time} remaining": "tem {remaining_time} restante",
    "you will have ": "disp\u00f5e apenas de",
    "your course": "o seu curso",
    "{num_of_hours} hour": "{num_of_hours} hora",
    "{num_of_hours} hours": "{num_of_hours} horas",
    "{num_of_minutes} minute": "{num_of_minutes} minuto",
    "{num_of_minutes} minutes": "{num_of_minutes} minutos"
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

