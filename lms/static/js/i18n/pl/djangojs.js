

(function (globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function (count) { return (count == 1) ? 0 : 1; };
  

  
  /* gettext library */

  django.catalog = {
    " menu to see a list of all topics.": " aby zobaczy\u0107 list\u0119 wszystkich temat\u00f3w.", 
    "%(comments_count)s %(span_sr_open)scomments %(span_close)s": "%(comments_count)s %(span_sr_open)s komentarze %(span_close)s", 
    "%(comments_count)s %(span_sr_open)scomments (%(unread_comments_count)s unread comments)%(span_close)s": "%(comments_count)s %(span_sr_open)skomentarze (%(unread_comments_count)s nieprzeczytane komentarze)%(span_close)s", 
    "%(post_type)s posted %(time_ago)s by %(author)s": "%(post_type)s opublikowano %(time_ago)s przez %(author)s", 
    "(Community TA)": "(Asystent spo\u0142eczno\u015bci)", 
    "(Staff)": "(Pracownicy)", 
    "(this post is about %(courseware_title_linked)s)": "(ten post jest o %(courseware_title_linked)s)", 
    "Add a Post": "Dodaj post", 
    "Add a Response": "Dodaj odpowied\u017a", 
    "Add a clear and descriptive title to encourage participation. (Required)": "Nadaj jasny i opisowy tytu\u0142, aby zach\u0119ci\u0107 do udzia\u0142u w dyskusji. (Wymagane)", 
    "Add a comment": "Dodaj komentarz", 
    "Add a response:": "Dodaj odpowied\u017a:", 
    "Add your post to a relevant topic to help others find it. (Required)": "Opublikuj sw\u00f3j post w\u015br\u00f3d powi\u0105zanych temat\u00f3w, aby innym \u0142atwiej by\u0142o go znale\u017a\u0107. (Wymagane)", 
    "Additional posts could not be loaded. Refresh the page and try again.": "Nie uda\u0142o si\u0119 wczyta\u0107 wi\u0119kszej liczby w\u0105tk\u00f3w. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "Additional responses could not be loaded. Refresh the page and try again.": "Nie uda\u0142o si\u0119 wczyta\u0107 dodatkowych odpowiedzi. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "All Groups": "Wszystkie grupy", 
    "All Posts": "Wszystkie posty", 
    "All Topics": "Wszystkie tematy", 
    "Announcements": "Og\u0142oszenia", 
    "Any divided discussion topics are divided based on cohort.": "Wszystkie rozdzielone dyskusje rozdzielono wg. grup kursant\u00f3w.", 
    "Any divided discussion topics are divided based on enrollment track.": "Wszystkie rozdzielone dyskusje rozdzielono wg. tor\u00f3w rejestracji", 
    "Are you sure you want to delete this comment?": "Czy na pewno chcesz usun\u0105\u0107 ten komentarz?", 
    "Are you sure you want to delete this post?": "Czy na pewno chcesz usun\u0105\u0107 ten post?", 
    "Are you sure you want to delete this response?": "Czy na pewno chcesz usun\u0105\u0107 t\u0119 odpowied\u017a?", 
    "Cancel": "Anuluj", 
    "Check this box to receive an email digest once a day notifying you about new, unread activity from posts you are following.": "Zaznacz to pole, aby otrzymywa\u0107 codzienny e-mail z powiadomieniami o nowych, nieprzeczytanych odpowiedziach pod postami, kt\u00f3re \u015bledzisz.", 
    "Close": "Zamknij", 
    "Closed": "Zamkni\u0119te", 
    "Cohorts": "Grupy kursant\u00f3w", 
    "Community TA": "Asystent spo\u0142eczno\u015bci", 
    "Current conversation": "Bie\u017c\u0105ca konwersacja", 
    "Delete": "Usu\u0144", 
    "Delete this team?": "Usun\u0105\u0107 ten zesp\u00f3\u0142?", 
    "Deleting a team is permanent and cannot be undone. All members are removed from the team, and team discussions can no longer be accessed.": "Usuni\u0119cie zespo\u0142u jest trwa\u0142e i nie mo\u017cna go b\u0119dzie cofn\u0105\u0107. Wszyscy cz\u0142onkowie zostan\u0105 wydaleni z zespo\u0142u i nie b\u0119dzie mo\u017cna ju\u017c otworzy\u0107 dyskusji zespo\u0142u.", 
    "Discussion": "Dyskusja", 
    "Discussion Home": "Strona g\u0142\u00f3wna dyskusji", 
    "Discussion admins, moderators, and TAs can make their posts visible to all students or specify a single group.": "Administratorzy dyskusji, moderatorzy i asystenci kursu mog\u0105 ustawi\u0107 widoczno\u015b\u0107 swoich post\u00f3w dla wszystkich student\u00f3w lub dla pojedynczej grupy.", 
    "Discussion topics in the course are not divided.": "Tematy dyskusji na tym kursie nie s\u0105 w tej chwili rozdzielone.", 
    "Discussions": "Dyskusje", 
    "Discussions are unified; all learners interact with posts from other learners, regardless of the group they are in.": "Dyskusje s\u0105 ujednolicone. Ka\u017cdy ucze\u0144 mo\u017ce reagowa\u0107 na posty dowolnego innego ucznia, bez wzgl\u0119du na podzia\u0142y grupowe.", 
    "Divided": "Rozdzielono", 
    "Earn points for your engagement by adding a new post of responding to an existing post.": "Zwi\u0119ksz swoj\u0105 punktacj\u0119 \u201ePoziomu zaanga\u017cowania\u201d, publikuj\u0105c nowe posty lub odpowiedzi do ju\u017c istniej\u0105cych.", 
    "Edit": "Edytuj", 
    "Edit your post below.": "Edytuj post poni\u017cej", 
    "Editing comment": "Edytowanie komentarza", 
    "Editing post": "Edytowanie postu", 
    "Editing response": "Edytowanie odpowiedzi", 
    "Endorse": "Poprzyj", 
    "Engage with posts": "Reaguj na posty", 
    "Enrollment Tracks": "Tory rejestracji", 
    "Error": "B\u0142\u0105d", 
    "Error posting your message.": "Nie uda\u0142o si\u0119 opublikowa\u0107 Twojej wiadomo\u015bci.", 
    "Filter and sort topics": "Filtruj i sortuj tematy", 
    "Find discussions": "Znajd\u017a dyskusje", 
    "Follow": "\u015aled\u017a", 
    "Follow or unfollow posts": "\u015aled\u017a lub przesta\u0144 \u015bledzi\u0107 posty", 
    "Following": "\u015aledzisz", 
    "Group Work": "Group Work", 
    "Hide Discussion": "Ukryj dyskusj\u0119", 
    "How to use %(platform_name)s discussions": "Jak pos\u0142ugiwa\u0107 si\u0119 dyskusjami %(platform_name)s", 
    "How to use discussions": "Jak pos\u0142ugiwa\u0107 si\u0119 dyskusjami", 
    "If you leave, you can no longer post in this team's discussions. Your place will be available to another learner.": "Je\u015bli opu\u015bcisz, nie b\u0119dziesz m\u00f3g\u0142 ju\u017c publikowa\u0107 post\u00f3w w dyskusjach tego zespo\u0142u. Twoje miejsce zostanie udost\u0119pnione innym uczniom.", 
    "Leaderboards": "Rankingi lider\u00f3w", 
    "Load all responses": "Wczytaj wszystkie odpowiedzi", 
    "Load more": "Za\u0142aduj wi\u0119cej", 
    "Load next {numResponses} responses": "Wczytaj nast\u0119pnych {numResponses} odpowiedzi", 
    "Loading content": "Wczytywanie zawarto\u015bci", 
    "Loading more threads": "Wczytywanie wi\u0119kszej liczby w\u0105tk\u00f3w", 
    "Loading posts list": "Wczytywanie listy post\u00f3w", 
    "Mark as Answer": "Zaznacz jako odpowied\u017a", 
    "More": "Wi\u0119cej", 
    "Next": "Nast\u0119pny", 
    "No posts matched your query.": "Nie znaleziono post\u00f3w pasuj\u0105cych do Twojego zapytania.", 
    "No results found for {original_query}. Showing results for {suggested_query}.": "Nie znaleziono wynik\u00f3w dla {original_query}, Pokazywanie wynik\u00f3w dla {suggested_query}.", 
    "Not divided": "Nie rozdzielono", 
    "OK": "OKOK", 
    "Open": "Otw\u00f3rz", 
    "Other": "Inne", 
    "Pin": "Przypnij", 
    "Pinned": "Przypi\u0119te", 
    "Post type": "Typ postu", 
    "Previous": "Poprzedni", 
    "Question": "Pytanie", 
    "Questions raise issues that need answers. Discussions share ideas and start conversations. (Required)": "Pytania podnosz\u0105 kwestie wymagaj\u0105ce odpowiedzi. Dyskusje s\u0142u\u017c\u0105 do dzielenie si\u0119 opiniami i rozpocz\u0119cia konwersacji. (Wymagane)", 
    "Receive updates": "Otrzymuj powiadomienia", 
    "Related to: %(courseware_title_linked)s": "Powi\u0105zane z: %(courseware_title_linked)s", 
    "Report": "Zg\u0142o\u015b", 
    "Report abuse": "Zg\u0142o\u015b naruszenie", 
    "Report abuse, topics, and responses": "Zg\u0142aszaj naruszenia, nieodpowiednie tematy i odpowiedzi", 
    "Reported": "Zg\u0142oszono", 
    "Responses could not be loaded. Refresh the page and try again.": "Nie uda\u0142o si\u0119 wczyta\u0107 odpowiedzi. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "Save": "Zapisz", 
    "Search": "Szukaj", 
    "Search all posts": "Przeszukaj wszystkie posty", 
    "Search and filter all posts to find specific topics or posts.": "Wyszukuj i filtruj wszystkie posty, aby znale\u017a\u0107 konkretne tematy lub posty.", 
    "Show Comment (%(num_comments)s)": [
      "Poka\u017c komentarz (%(num_comments)s)", 
      "Poka\u017c komentarze (%(num_comments)s)"
    ], 
    "Show Discussion": "Poka\u017c dyskusj\u0119", 
    "Show posts by {username}.": "Poka\u017c posty wg. {username}.", 
    "Showing all responses": "Pokazuje wszystkie odpowiedzi", 
    "Showing first response": [
      "Pokazuje pierwsz\u0105 odpowied\u017a", 
      "Pokazuje pierwszych {numResponses} odpowiedzi"
    ], 
    "Some images in this post have been omitted": "Niekt\u00f3re obrazy w tym po\u015bcie zosta\u0142 pomini\u0119te", 
    "Staff": "Pracownicy", 
    "Submit": "Prze\u015blij", 
    "Team \"{team}\" successfully deleted.": "Pomy\u015blnie usuni\u0119to zesp\u00f3\u0142 \u201e{team}\u201d", 
    "The post you selected has been deleted.": "Post, kt\u00f3ry wybra\u0142e\u015b zosta\u0142 usuni\u0119ty.", 
    "This comment could not be deleted. Refresh the page and try again.": "Nie uda\u0142o si\u0119 usun\u0105\u0107 komentarza. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This discussion could not be loaded. Refresh the page and try again.": "Nie uda\u0142o si\u0119 wczyta\u0107 dyskusji. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post could not be closed. Refresh the page and try again.": "Nie uda\u0142o si\u0119 zamkn\u0105\u0107 postu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post could not be flagged for abuse. Refresh the page and try again.": "Nie uda\u0142o si\u0119 oznaczy\u0107 postu jako nieodpowiedniego. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post could not be pinned. Refresh the page and try again.": "Nie uda\u0142o si\u0119 przypi\u0105\u0107 postu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post could not be reopened. Refresh the page and try again.": "Nie uda\u0142o si\u0119 ponownie otworzy\u0107 postu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post could not be unflagged for abuse. Refresh the page and try again.": "Nie uda\u0142o si\u0119 cofn\u0105\u0107 oznaczenia postu jako nieodpowiedniego. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post could not be unpinned. Refresh the page and try again.": "Nie uda\u0142o si\u0119 odpi\u0105\u0107 postu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "This post is visible only to %(group_name)s.": "Ten post jest widoczny tylko dla %(group_name)s.", 
    "This post is visible to everyone.": "Ten post jest widoczny dla wszystkich.", 
    "This response could not be marked as an answer. Refresh the page and try again.": "Nie mo\u017cna oznaczy\u0107 tej odpowiedzi. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie", 
    "This response could not be marked as endorsed. Refresh the page and try again.": "Nie mo\u017cna oznaczy\u0107 tej odpowiedzi jako polecanej. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie", 
    "This response could not be unendorsed. Refresh the page and try again.": "Nie mo\u017cna cofn\u0105\u0107 polecenia. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie", 
    "This response could not be unmarked as an answer. Refresh the page and try again.": "Nie mo\u017cna odznaczy\u0107 tej odpowiedzi. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie", 
    "This thread is closed.": "Ten w\u0105tek jest zamkni\u0119ty.", 
    "This vote could not be processed. Refresh the page and try again.": "Nie uda\u0142o si\u0119 da\u0107 punktu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "Title": "Tytu\u0142", 
    "Today at ": "Dzisiaj ", 
    "Toggle Notifications Setting": "Ustawienie \u201eW\u0142\u0105cz powiadomienia\u201d", 
    "Topic area": "Obszar tematyczny", 
    "Unendorse": "Przesta\u0144 popiera\u0107", 
    "Unfollow": "Przesta\u0144 \u015bledzi\u0107", 
    "Unmark as Answer": "Odznacz jako odpowied\u017a", 
    "Unpin": "Odepnij", 
    "Unreport": "Cofnij zg\u0142oszenie", 
    "Update comment": "Zaktualizuj komentarz", 
    "Update post": "Zaktualizuj post", 
    "Update response": "Zaktualizuj odpowied\u017a", 
    "Use cohorts as the basis for dividing discussions. All learners, regardless of cohort, see the same discussion topics, but within divided topics, only members of the same cohort see and respond to each others\u2019 posts. ": "Rozdziel dyskusje wg. grup kursant\u00f3w. Wszyscy uczniowie, bez wzgl\u0119du tor rejestracji, mog\u0105 zobaczy\u0107 te same tematy dyskusji, ale wewn\u0105trz podzielonych temat\u00f3w, tylko uczniowie z tej samej grupy kursant\u00f3w mog\u0105 zobaczy\u0107 i odpowiada\u0107 na posty innych.", 
    "Use enrollment tracks as the basis for dividing discussions. All learners, regardless of their enrollment track, see the same discussion topics, but within divided topics, only learners who are in the same enrollment track see and respond to each others\u2019 posts.": "Rozdziel dyskusje wg. tor\u00f3w rejestracji. Wszyscy uczniowie, bez wzgl\u0119du tor rejestracji, mog\u0105 zobaczy\u0107 te same tematy dyskusji, ale wewn\u0105trz podzielonych temat\u00f3w, tylko uczniowie z tego samego toru rejestracji mog\u0105 zobaczy\u0107 i odpowiada\u0107 na posty innych.", 
    "Use the": "U\u017cyj menu", 
    "Use the All Topics menu to find specific topics.": "U\u017cyj menu \u201eWszystkie tematy\u201d, aby znale\u017a\u0107 konkretny temat", 
    "View discussion": "Zobacz dyskusj\u0119", 
    "Visible to": "Widoczne dla", 
    "Vote for good posts and responses": "Przyznawaj punkty dobrym postom i odpowiedziom", 
    "Vote for goods post and responses": "Przyznawaj punkty dobrym postom i odpowiedziom", 
    "Vote for this post,": "Przyznaj temu postowi punkt", 
    "We have encountered an error. Refresh your browser and then try again.": "Wyst\u0105pi\u0142 b\u0142\u0105d. Od\u015bwie\u017c przegl\u0105dark\u0119 i spr\u00f3buj ponownie.", 
    "We've encountered an error. Refresh your browser and then try again.": "Wyst\u0105pi\u0142 b\u0142\u0105d. Od\u015bwie\u017c przegl\u0105dark\u0119 i spr\u00f3buj ponownie.", 
    "You are not permitted to view this discussion.": "Nie mo\u017cesz zobaczy\u0107 tej dyskusji.", 
    "You are now": "Obecnie jeste\u015b", 
    "You could not be subscribed to this post. Refresh the page and try again.": "Nie mo\u017cesz zacz\u0105\u0107 \u015bledzi\u0107 tego postu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "You could not be unsubscribed from this post. Refresh the page and try again.": "Nie mo\u017cesz przesta\u0107 \u015bledzi\u0107 tego postu. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "Your changes have been saved.": "Twoje zmiany zosta\u0142y zapisane. {details}", 
    "Your changes have been saved. {details}": "Twoje zmiany zosta\u0142y zapisane. {details}", 
    "Your post will be discarded.": "Tw\u00f3j post zostanie odrzucony", 
    "Your question or idea (required)": "Twoje pytanie o pomys\u0142 (wymagane)", 
    "Your request could not be processed. Refresh the page and try again.": "Nie uda\u0142o si\u0119 przetworzy\u0107 Twojego \u017c\u0105dania. Od\u015bwie\u017c stron\u0119 i spr\u00f3buj ponownie.", 
    "anonymous": "u\u017cytkownik anonimowy", 
    "answered question": "pytanie posiadaj\u0105ce odpowied\u017a", 
    "discussion": "dyskusja", 
    "discussion posted": "opublikowana dyskusja", 
    "discussion posted %(time_ago)s by %(author)s": "opublikowana dyskusja %(time_ago)s przez %(author)s", 
    "endorsed %(time_ago)s": "polecane %(time_ago)s", 
    "endorsed %(time_ago)s by %(user)s": "polecane %(time_ago)s przez %(user)s", 
    "engage with posts": "reaguj na posty", 
    "find discussions": "znajd\u017a dyskusje", 
    "follow this post": "\u015bled\u017a ten post", 
    "for": "na", 
    "image omitted": "obraz pomini\u0119ty", 
    "in the cohort!": "w grupie kursant\u00f3w!", 
    "marked as answer %(time_ago)s": "oznaczono jako odpowied\u017a %(time_ago)s", 
    "marked as answer %(time_ago)s by %(user)s": "oznacz jako odpowied\u017a %(time_ago)s przez %(user)s", 
    "post anonymously": "opublikuj anonimowo", 
    "post anonymously to classmates": "opublikuj anonimowo dla koleg\u00f3w z kursu", 
    "posted %(time_ago)s by %(author)s": "opublikowano %(time_ago)s przez %(author)s", 
    "question posted %(time_ago)s by %(author)s": "opublikowane pytanie %(time_ago)s przez %(author)s", 
    "there is currently {numVotes} vote": [
      "aktualna liczba punkt\u00f3w to: {numVotes}", 
      "aktualna liczba punkt\u00f3w to: {numVotes}"
    ], 
    "unanswered question": "pytanie bez odpowiedzi", 
    "{numResponses} other response": [
      "{numResponses} inna odpowied\u017a", 
      "{numResponses} innych odpowiedzi"
    ], 
    "{numResponses} response": [
      "{numResponses} odpowied\u017a", 
      "{numResponses} odpowiedzi"
    ], 
    "{numVotes} Vote": [
      "{numVotes} Punkt", 
      "{numVotes} Punkty"
    ], 
    "{unread_comments_count} new": "{unread_comments_count} nowe"
  };

  django.gettext = function (msgid) {
    var value = django.catalog[msgid];
    if (typeof(value) == 'undefined') {
      return msgid;
    } else {
      return (typeof(value) == 'string') ? value : value[0];
    }
  };

  django.ngettext = function (singular, plural, count) {
    var value = django.catalog[singular];
    if (typeof(value) == 'undefined') {
      return (count == 1) ? singular : plural;
    } else {
      return value[django.pluralidx(count)];
    }
  };

  django.gettext_noop = function (msgid) { return msgid; };

  django.pgettext = function (context, msgid) {
    var value = django.gettext(context + '\x04' + msgid);
    if (value.indexOf('\x04') != -1) {
      value = msgid;
    }
    return value;
  };

  django.npgettext = function (context, singular, plural, count) {
    var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
    if (value.indexOf('\x04') != -1) {
      value = django.ngettext(singular, plural, count);
    }
    return value;
  };
  

  django.interpolate = function (fmt, obj, named) {
    if (named) {
      return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
    } else {
      return fmt.replace(/%s/g, function(match){return String(obj.shift())});
    }
  };


  /* formatting library */

  django.formats = {
    "DATETIME_FORMAT": "j E Y H:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S", 
      "%d.%m.%Y %H:%M:%S.%f", 
      "%d.%m.%Y %H:%M", 
      "%d.%m.%Y", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d"
    ], 
    "DATE_FORMAT": "j E Y", 
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y", 
      "%d.%m.%y", 
      "%y-%m-%d", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d-m-Y  H:i", 
    "SHORT_DATE_FORMAT": "d-m-Y", 
    "THOUSAND_SEPARATOR": "\u00a0", 
    "TIME_FORMAT": "H:i", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M:%S.%f", 
      "%H:%M"
    ], 
    "YEAR_MONTH_FORMAT": "F Y"
  };

  django.get_format = function (format_type) {
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

}(this));

