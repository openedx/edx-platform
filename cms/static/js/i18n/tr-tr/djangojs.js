

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
    "\n                    Your verification attempt failed. Please read our guidelines to make\n                    sure you understand the requirements for successfully completing verification,\n                    then try again.\n                ": "\n                    Do\u011frulama denemeniz ba\u015far\u0131s\u0131z oldu. L\u00fctfen ba\u015far\u0131l\u0131 bir do\u011frulama i\u015flemi i\u00e7in\n                    yerine getirilmesi gerekenleri do\u011frulamak i\u00e7in k\u0131lavuz metinlerimizi yeniden okuyun,\n                    ve ard\u0131ndan tekrar deneyin.\n                ", 
    "\n                    Your verification has expired. You must successfully complete a new identity verification\n                    before you can start the proctored exam.\n                ": "\n                    Do\u011frulaman\u0131z ge\u00e7erlili\u011fini kaybetti. G\u00f6zetmenli s\u0131nava ba\u015flamadan \u00f6nce\n                    yeni bir kimlik do\u011frulamas\u0131 yapmal\u0131s\u0131n\u0131z.\n                ", 
    "\n                Complete your verification before starting the proctored exam.\n            ": "\n                G\u00f6zetmenli s\u0131nava ba\u015flamadan \u00f6nce kimlik do\u011frulaman\u0131z\u0131 tamamlay\u0131n.\n            ", 
    "\n          Start my exam\n        ": "\n          S\u0131nav\u0131m\u0131 ba\u015flat\n        ", 
    "\n        1. Copy this unique exam code. You will be prompted to paste this code later before you start the exam.\n      ": "\n        1. Bu e\u015fsiz s\u0131nav kodunu kopyalay\u0131n. S\u0131nava ba\u015flarken bu kodu girmenizi isteyen bir uyar\u0131 g\u00f6receksiniz.\n      ", 
    "\n        2. Follow the link below to set up proctoring.\n      ": "\n        2. G\u00f6zetmenli s\u0131nav\u0131 ayarlamak i\u00e7in a\u015fa\u011f\u0131daki ba\u011flant\u0131y\u0131 kopyalay\u0131n.\n      ", 
    "\n        A new window will open. You will run a system check before downloading the proctoring application.\n      ": "\n        Yeni bir pencere a\u00e7\u0131lacak. G\u00f6zetmen uygulamas\u0131n\u0131 indirmeden \u00f6nce bir sistem denetimi yap\u0131lacak.\n      ", 
    "\n        About Proctored Exams\n        ": "\n        G\u00f6zetmenli S\u0131navlar Hakk\u0131nda\n        ", 
    "\n        Are you sure you want to take this exam without proctoring?\n      ": "\n        Bu s\u0131nav\u0131 g\u00f6zetmensiz olarak almak istedi\u011finize emin misiniz?\n      ", 
    "\n        Due to unsatisfied prerequisites, you can only take this exam without proctoring.\n      ": "\n        Kar\u015f\u0131lanmayan \u00f6n gerekliler y\u00fcz\u00fcnden, bu s\u0131nav\u0131 sadece g\u00f6zetmensiz olarak alabilirsiniz.\n      ", 
    "\n        I am not interested in academic credit.\n      ": "\n       Akademik krediyle ilgilenmiyorum.\n      ", 
    "\n        I am ready to start this timed exam.\n      ": "\n        S\u00fcre s\u0131n\u0131rl\u0131 bu s\u0131nava ba\u015flamaya haz\u0131r\u0131m.\n      ", 
    "\n        If you take this exam without proctoring, you will <strong> no longer be eligible for academic credit. </strong>\n      ": "\n        Bu s\u0131nav\u0131 g\u00f6zetmensiz olarak alman\u0131z durumunda, <strong> akademik krediye hak kazanamayacaks\u0131n\u0131z.</strong>\n      ", 
    "\n        No, I want to continue working.\n      ": "\n        Hay\u0131r, \u00e7al\u0131\u015fmaya devam edece\u011fim.\n      ", 
    "\n        No, I'd like to continue working\n      ": "\n        Hay\u0131r, \u00e7al\u0131\u015fmaya devam edece\u011fim\n      ", 
    "\n        Select the exam code, then copy it using Command+C (Mac) or Control+C (Windows).\n      ": "\n        S\u0131nav kodunu se\u00e7in, ard\u0131ndan Command+C (Mac) veya Control+C (Windows) ile kopyalay\u0131n.\n      ", 
    "\n        You have submitted your timed exam.\n      ": "\n        S\u00fcre s\u0131n\u0131rl\u0131 s\u0131nav\u0131n\u0131z\u0131 g\u00f6nderdiniz.\n      ", 
    "\n        You will be guided through steps to set up online proctoring software and to perform various checks.\n      ": "\n        G\u00f6zetmen yaz\u0131l\u0131m\u0131n\u0131n ayarlanmas\u0131n\u0131n her bir adam\u0131nda size rehberlik edilecek ve \u00e7e\u015fitli denetimler yap\u0131lacak.\n      ", 
    "\n      Are you sure you want to end your proctored exam?\n    ": "\n      G\u00f6zetmenli s\u0131nav\u0131n\u0131z\u0131 sona erdirmek istedi\u011finize emin misiniz?\n    ", 
    "\n      Error with proctored exam\n    ": "\n     G\u00f6zetmenli s\u0131navda hata\n    ", 
    "\n      Follow these instructions\n    ": "\n      Bu y\u00f6nergeleri izleyin\n    ", 
    "\n      Follow these steps to set up and start your proctored exam.\n    ": "\n      G\u00f6zetmenli s\u0131nav\u0131n\u0131z\u0131 ayarlamak ve ba\u015flatmak i\u00e7in a\u015fa\u011f\u0131daki ad\u0131mlar\u0131 takip edin.\n    ", 
    "\n      Get familiar with proctoring for real exams later in the course. This practice exam has no impact\n      on your grade in the course.\n    ": "\n      Ders sonras\u0131 ger\u00e7ek s\u0131navlar i\u00e7in g\u00f6zetmenli s\u0131navlar\u0131 deneyimleyin.\n      Al\u0131\u015ft\u0131rma s\u0131nav\u0131 ders notunuzu etkilemeyecek.\n    ", 
    "\n      If you have disabilities,\n      you might be eligible for an additional time allowance on timed exams.\n      Ask your course team for information about additional time allowances.\n    ": "\n      Bedensel engellerinizin olmas\u0131 halinde,\n      zaman s\u0131n\u0131rl\u0131 s\u0131navlar i\u00e7in ek s\u00fcre talep edebilirsiniz.\n      Ek s\u00fcre talepleri i\u00e7in gerekli ko\u015fullar\u0131 ders tak\u0131m\u0131n\u0131zdan \u00f6\u011frenebilirsiniz.\n    ", 
    "\n      Practice exams do not affect your grade or your credit eligibility.\n      You have completed this practice exam and can continue with your course work.\n    ": "\n      Al\u0131\u015ft\u0131rma s\u0131navlar\u0131 ders notunuzu ya da kredilerinizi etkilemez.\n      Bu al\u0131\u015ft\u0131rma s\u0131nav\u0131n\u0131 tamamlad\u0131n\u0131z ve dersinize kald\u0131\u011f\u0131n\u0131z yerden devam edebilirsiniz.\n    ", 
    "\n      The due date for this exam has passed\n    ": "\n      Bu s\u0131nav i\u00e7in teslim tarihi ge\u00e7ti\n    ", 
    "\n      There was a problem with your practice proctoring session\n    ": "\n     G\u00f6zetmenli al\u0131\u015ft\u0131rma oturumunuzda bir hata ger\u00e7ekle\u015fti\n    ", 
    "\n      This exam is proctored\n    ": "\n      Bu s\u0131nav g\u00f6zetmenlidir\n    ", 
    "\n      Try a proctored exam\n    ": "\n      G\u00f6zetmenli s\u0131nav dene\n    ", 
    "\n      Yes, end my proctored exam\n    ": "\n      Evet, g\u00f6zetmenli s\u0131nav\u0131m\u0131 sona erdir\n    ", 
    "\n      Yes, submit my timed exam.\n    ": "\n      Evet, s\u00fcre s\u0131n\u0131rl\u0131 s\u0131nav\u0131m\u0131 g\u00f6nder.\n    ", 
    "\n      You have submitted this practice proctored exam\n    ": "\n      Bu g\u00f6zetmenli al\u0131\u015ft\u0131rma s\u0131nav\u0131n\u0131 g\u00f6nderdiniz\n    ", 
    "\n      You have submitted this proctored exam for review\n    ": "\n      G\u00f6zetmenli s\u0131nav\u0131n\u0131z\u0131 inceleme i\u00e7in g\u00f6nderdiniz\n    ", 
    "\n      Your practice proctoring results: <b class=\"failure\"> Unsatisfactory </b>\n    ": "\n      Al\u0131\u015ft\u0131rma s\u0131nav\u0131 sonucunuz: <b class=\"failure\"> Ba\u015far\u0131s\u0131z </b>\n    ", 
    "\n      Your proctoring session was reviewed and did not pass requirements\n    ": "\n      G\u00f6zetmenli oturumunuz incelendi ve gereklilikleri yerine getirmedi\u011finiz i\u00e7in ge\u00e7emediniz\n    ", 
    "\n      Your proctoring session was reviewed and passed all requirements\n    ": "\n      G\u00f6zetmenli oturumunuz incelendi ve t\u00fcm gereklilikleri yerine getirdiniz\n    ", 
    "\n    You did not satisfy the following prerequisites:\n    ": "\n    A\u015fa\u011f\u0131daki \u00f6n gereklilikleri kar\u015f\u0131lam\u0131yorsunuz:\n    ", 
    " Your Proctoring Session Has Started ": "G\u00f6zetmenli S\u0131nav Oturumunuz Ba\u015flad\u0131", 
    " and {num_of_minutes} minute": " ve {num_of_minutes} dakika", 
    " and {num_of_minutes} minutes": " ve {num_of_minutes} dakika", 
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s / %(cnt)s se\u00e7ildi", 
      "%(sel)s / %(cnt)s se\u00e7ildi"
    ], 
    "(required):": "(gerekli):", 
    "6 a.m.": "Sabah 6", 
    "6 p.m.": "6 \u00f6.s.", 
    "Additional Time (minutes)": "Ek Zaman (dakika)", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Yeni dosya y\u00fcklemeleriniz eskilerinin \u00fczerine yazacak. Devam etmek istedi\u011finize emin misiniz?", 
    "All Unreviewed": "T\u00fcm \u0130ncelenmeyenler", 
    "All Unreviewed Failures": "T\u00fcm \u0130ncelenmemi\u015f Hatalar", 
    "April": "Nisan", 
    "Assessment": "De\u011ferlendirme", 
    "Assessments": "De\u011ferlendirmeler", 
    "August": "A\u011fustos", 
    "Available %s": "Mevcut %s", 
    "Back to Full List": "Tam Listeye D\u00f6n", 
    "Block view is unavailable": "Blok g\u00f6r\u00fcn\u00fcm mevcut de\u011fil", 
    "Can I request additional time to complete my exam?": "S\u0131nav\u0131m\u0131 tamamlamak i\u00e7in ekstra zaman isteyebilir miyim?", 
    "Cancel": "\u0130ptal", 
    "Cannot Start Proctored Exam": "G\u00f6zetmenli S\u0131nav Ba\u015flat\u0131lam\u0131yor", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "G\u00f6revin bir par\u00e7as\u0131 olarak se\u00e7ili olmayan ad\u0131mlardaki de\u011fi\u015fiklikler kaydedilmeyecek.", 
    "Choose": "Se\u00e7in", 
    "Choose a Date": "Bir Tarih Se\u00e7in", 
    "Choose a Time": "Bir Saat Se\u00e7in", 
    "Choose a time": "Bir saat se\u00e7in", 
    "Choose all": "T\u00fcm\u00fcn\u00fc se\u00e7in", 
    "Chosen %s": "Se\u00e7ilen %s", 
    "Click to choose all %s at once.": "Bir kerede t\u00fcm %s se\u00e7ilmesi i\u00e7in t\u0131klay\u0131n.", 
    "Click to remove all chosen %s at once.": "Bir kerede t\u00fcm se\u00e7ilen %s kald\u0131r\u0131lmas\u0131 i\u00e7in t\u0131klay\u0131n.", 
    "Close": "Kapat", 
    "Continue Exam Without Proctoring": "S\u0131nava G\u00f6zetmensiz Olarak Devam Et", 
    "Continue to Verification": "Do\u011frulamaya Devam Et", 
    "Continue to my practice exam": "Al\u0131\u015ft\u0131rma s\u0131nav\u0131ma devam et", 
    "Could not retrieve download url.": "\u0130ndirme linkine eri\u015filemedi.", 
    "Could not retrieve upload url.": "Y\u00fckleme URL'ine eri\u015filemedi.", 
    "Couldn't Save This Assignment": "Bu G\u00f6rev Kaydedilemedi", 
    "Course Id": "Ders No", 
    "Created": "Olu\u015fturuldu", 
    "Criterion Added": "\u00d6l\u00e7\u00fct Eklendi", 
    "Criterion Deleted": "\u00d6l\u00e7\u00fct Silindi", 
    "December": "Aral\u0131k", 
    "Declined": "Reddedildi", 
    "Describe ": "Tan\u0131mla", 
    "Do you want to upload your file before submitting?": " G\u00f6ndermeden \u00f6nce dosyan\u0131z\u0131 y\u00fcklemek istiyor musunuz?", 
    "Doing so means that you are no longer eligible for academic credit.": "Bu \u015fekilde yapmak, akademik kredinizi dolduramayaca\u011f\u0131n\u0131z anlam\u0131na gelir.", 
    "Download Software Clicked": "Yaz\u0131l\u0131m \u0130ndir'e T\u0131kland\u0131", 
    "Error": "Hata", 
    "Error getting the number of ungraded responses": "Notland\u0131r\u0131lmam\u0131\u015f cevaplar\u0131n say\u0131s\u0131n\u0131 \u00e7ekmede hata", 
    "Failed Proctoring": "Ba\u015far\u0131s\u0131z G\u00f6zetmenli S\u0131nav", 
    "February": "\u015eubat", 
    "Feedback available for selection.": "Se\u00e7ilenler i\u00e7in geri bildirim m\u00fcmk\u00fcn.", 
    "File size must be 10MB or less.": "Dosya boyutu 10MB veya daha az olmal\u0131.", 
    "File type is not allowed.": "Dosya t\u00fcr\u00fcne izin verilmiyor.", 
    "File types can not be empty.": "Dosya t\u00fcr\u00fc bo\u015f olamaz.", 
    "Filter": "S\u00fczge\u00e7", 
    "Final Grade Received": "Final Notu Al\u0131nd\u0131", 
    "Go Back": "Geri D\u00f6n", 
    "Heading 3": "Ba\u015fl\u0131k 3", 
    "Heading 4": "Ba\u015fl\u0131k 4", 
    "Heading 5": "Ba\u015fl\u0131k 5", 
    "Heading 6": "Ba\u015fl\u0131k 6", 
    "Hide": "Gizle", 
    "I am ready to start this timed exam,": "S\u00fcre s\u0131n\u0131rl\u0131 bu s\u0131nava ba\u015flamaya haz\u0131r\u0131m,", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "E\u011fer sayfadan cevab\u0131n\u0131z\u0131 kaydetmeden ya da g\u00f6ndermeden ayr\u0131l\u0131rsan\u0131z, cevap i\u00e7in yapt\u0131\u011f\u0131n\u0131z i\u015flemleri kaybedeceksiniz.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Bu sayfay\u0131 de\u011ferlendirmenizi yazmadan terk etmeniz durumunda, yapt\u0131\u011f\u0131n\u0131z t\u00fcm i\u015fleri kaybedeceksiniz.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Bu sayfay\u0131 ekip de\u011ferlendirmenizi yazmadan terk etmeniz durumunda, yapt\u0131\u011f\u0131n\u0131z t\u00fcm i\u015fleri kaybedeceksiniz.", 
    "Is Sample Attempt": "Bir \u00d6rnek Denemedir", 
    "January": "Ocak", 
    "July": "Temmuz", 
    "June": "Haziran", 
    "List of Open Assessments is unavailable": "A\u00e7\u0131k G\u00f6revler listesi mevcut de\u011fil", 
    "March": "Mart", 
    "May": "May\u0131s", 
    "Midnight": "Geceyar\u0131s\u0131", 
    "Noon": "\u00d6\u011fle", 
    "Not Selected": "Se\u00e7ilmedi", 
    "Note: You are %s hour ahead of server time.": [
      "Not: Sunucu saatinin %s saat ilerisindesiniz.", 
      "Not: Sunucu saatinin %s saat ilerisindesiniz."
    ], 
    "Note: You are %s hour behind server time.": [
      "Not: Sunucu saatinin %s saat gerisindesiniz.", 
      "Not: Sunucu saatinin %s saat gerisindesiniz."
    ], 
    "November": "Kas\u0131m", 
    "Now": "\u015eimdi", 
    "October": "Ekim", 
    "One or more rescheduling tasks failed.": "Bir veya daha fazla yeniden zamanlama g\u00f6revi ba\u015far\u0131s\u0131z oldu.", 
    "Option Deleted": "Se\u00e7enek Silindi", 
    "Paragraph": "Paragraf", 
    "Passed Proctoring": "Ba\u015far\u0131l\u0131 G\u00f6zetmenli S\u0131nav", 
    "Peer": "Ki\u015fi", 
    "Pending Session Review": "Bekleyen Oturum \u0130ncelemesi", 
    "Please correct the outlined fields.": "L\u00fctfen alt\u0131 \u00e7izili alanlar\u0131 d\u00fczeltin.", 
    "Please wait": "L\u00fctfen bekleyin", 
    "Practice Exam Completed": "Al\u0131\u015ft\u0131rma S\u0131nav\u0131 Tamamland\u0131", 
    "Practice Exam Failed": "Al\u0131\u015ft\u0131rma S\u0131nav\u0131 Ba\u015far\u0131s\u0131z", 
    "Preformatted": "\u00d6nceden bi\u00e7imlendirilmi\u015f", 
    "Proctored Option Available": "G\u00f6zetmenli Se\u00e7enek Mevcut", 
    "Proctored Option No Longer Available": "G\u00f6zetmenli Se\u00e7enek Art\u0131k Mevcut De\u011fil", 
    "Proctoring Session Results Update for {course_name} {exam_name}": "{course_name} dersi {exam_name} s\u0131nav\u0131 i\u00e7in G\u00f6zetmenli S\u0131nav Sonu\u00e7lar\u0131 G\u00fcncellemesi", 
    "Ready To Start": "Ba\u015flamaya Haz\u0131r", 
    "Ready To Submit": "G\u00f6ndermeye Haz\u0131r", 
    "Rejected": "Reddedildi", 
    "Remove": "Kald\u0131r", 
    "Remove all": "T\u00fcm\u00fcn\u00fc kald\u0131r", 
    "Retry Verification": "Yeniden Do\u011frulama", 
    "Review Policy Exception": "\u0130nceleme Politikas\u0131 \u0130stisnas\u0131", 
    "Saving...": "Kaydediliyor...", 
    "Second Review Required": "\u0130kinci Bir \u0130nceleme Gerekli", 
    "Self": "Kendin", 
    "September": "Eyl\u00fcl", 
    "Server error.": "Sunucu hatas\u0131.", 
    "Show": "G\u00f6ster", 
    "Staff": "Personel", 
    "Start Proctored Exam": "G\u00f6zetmenli S\u0131nava Ba\u015fla", 
    "Start System Check": "Sistem Denetimine Ba\u015fla", 
    "Started": "Ba\u015flad\u0131", 
    "Status of Your Response": "Cevab\u0131n\u0131z\u0131n Durumu", 
    "Submitted": "Girildi", 
    "Take this exam without proctoring.": "Bu s\u0131nav\u0131 g\u00f6zetmensiz olarak al.", 
    "Taking As Open Exam": "A\u00e7\u0131k S\u0131nav Olarak Al\u0131n\u0131yor", 
    "Taking As Proctored Exam": "G\u00f6zetmenli S\u0131nav Olarak Al\u0131n\u0131yor", 
    "Taking as Proctored": "G\u00f6zetmenli Olarak Al\u0131n\u0131yor", 
    "The following file types are not allowed: ": "A\u015fa\u011f\u0131daki dosya t\u00fcr\u00fcne izin  verilmiyor:", 
    "The server could not be contacted.": "Sunucu ile ba\u011flant\u0131 kurulamad\u0131.", 
    "The staff assessment form could not be loaded.": "Personel de\u011ferlendirme formu y\u00fcklenemedi.", 
    "The submission could not be removed from the grading pool.": "Y\u00fckleme not havuzundan kald\u0131r\u0131lamad\u0131.", 
    "This assessment could not be submitted.": "Bu de\u011ferlendirme g\u00f6nderilemedi.", 
    "This exam has a time limit associated with it.": "Bu s\u0131nava ba\u011fl\u0131 bir s\u00fcre s\u0131n\u0131r\u0131 bulunmaktad\u0131r.", 
    "This feedback could not be submitted.": "Bu geri bildirim g\u00f6nderilemedi.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Bu mevcut %s listesidir. A\u015fa\u011f\u0131daki kutudan baz\u0131lar\u0131n\u0131 i\u015faretleyerek ve ondan sonra iki kutu aras\u0131ndaki \"Se\u00e7in\" okuna t\u0131klayarak se\u00e7ebilirsiniz.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Bu se\u00e7ilen %s listesidir. A\u015fa\u011f\u0131daki kutudan baz\u0131lar\u0131n\u0131 i\u015faretleyerek ve ondan sonra iki kutu aras\u0131ndaki \"Kald\u0131r\" okuna t\u0131klayarak kald\u0131rabilirsiniz.", 
    "This problem could not be saved.": "Bu problem kaydedilemedi.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "Bu problem \u015fu anda yay\u0131mlanm\u0131\u015f bulunuyor. Bu durumda herhangi bir de\u011fi\u015fiklik sadece ileriki de\u011ferlendirmelerde uygulanacakt\u0131r.", 
    "This response could not be saved.": "Bu cevap kaydedilemedi.", 
    "This response could not be submitted.": "Bu cevap g\u00f6nderilemedi.", 
    "This response has been saved but not submitted.": "Bu cevap kaydedildi, ancak g\u00f6nderilmedi.", 
    "This response has not been saved.": "Bu cevap kaydedilmedi.", 
    "This section could not be loaded.": "Bu b\u00f6l\u00fcm y\u00fcklenemedi.", 
    "Thumbnail view of ": "K\u00fc\u00e7\u00fck resim", 
    "Timed Exam": "Zamanlanm\u0131\u015f S\u0131nav", 
    "Timed Out": "Zaman A\u015f\u0131m\u0131na U\u011frad\u0131", 
    "To pass this exam, you must complete the problems in the time allowed.": "Bu s\u0131navdan ge\u00e7mek i\u00e7in, problemleri size tan\u0131nan s\u00fcrede \u00e7\u00f6zmelisiniz.", 
    "Today": "Bug\u00fcn", 
    "Tomorrow": "Yar\u0131n", 
    "Total Responses": "Toplam Cevaplar", 
    "Training": "Al\u0131\u015ft\u0131rma", 
    "Try this practice exam again": "Al\u0131\u015ft\u0131rma s\u0131nav\u0131n\u0131 tekrar dene", 
    "Type into this box to filter down the list of available %s.": "Mevcut %s listesini s\u00fczmek i\u00e7in bu kutu i\u00e7ine yaz\u0131n.", 
    "Unable to load": "Y\u00fcklenemedi", 
    "Unexpected server error.": "Beklenmeyen sunucu hatas\u0131.", 
    "Ungraded Practice Exam": "Puanlanmam\u0131\u015f Al\u0131\u015ft\u0131rma S\u0131nav\u0131", 
    "Unit Name": "\u00dcnite \u0130smi", 
    "Units": "\u00dcniteler", 
    "Unnamed Option": "Adland\u0131r\u0131lmam\u0131\u015f Se\u00e7enek", 
    "Verified": "Onayland\u0131", 
    "View my exam": "S\u0131nav\u0131m\u0131 g\u00f6r\u00fcnt\u00fcle", 
    "Waiting": "Bekleniyor", 
    "Warning": "Uyar\u0131", 
    "Yesterday": "D\u00fcn", 
    "You can also retry this practice exam": "Bu al\u0131\u015ft\u0131rma s\u0131nav\u0131n\u0131 ayn\u0131 zamanda deneyebilirsiniz de", 
    "You can upload files with these file types: ": "Bu dosya t\u00fcrleriyle dosya y\u00fckleyebilirsiniz:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Bir \u00f6l\u00e7\u00fct eklediniz. \u00d6\u011frenci E\u011fitimi ad\u0131m\u0131nda, \u00f6l\u00e7\u00fct i\u00e7in bir se\u00e7enek se\u00e7melisiniz. Bunu yapmak i\u00e7inse, Ayarlar sekmesine t\u0131klay\u0131n\u0131z.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Bir \u00f6l\u00e7\u00fct sildiniz. Sistem, \u00d6\u011frenci E\u011fitimi ad\u0131m\u0131ndaki \u00f6rnek cevaplardan \u00f6l\u00e7\u00fct kald\u0131r\u0131ld\u0131.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Bu \u00f6l\u00e7\u00fct i\u00e7in t\u00fcm kriterleri sildiniz. Sistem, \u00d6\u011frenci E\u011fitimi ad\u0131m\u0131ndaki \u00f6rnek cevaplardan \u00f6l\u00e7\u00fct kald\u0131r\u0131ld\u0131.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Bir se\u00e7enek sildiniz. Sistem, \u00d6\u011frenci E\u011fitimi ad\u0131m\u0131nda yer alan \u00f6rnek cevaplardaki \u00f6l\u00e7\u00fctten bu se\u00e7enek kald\u0131r\u0131ld\u0131. Bu \u00f6l\u00e7\u00fct i\u00e7in yeni bir se\u00e7enek se\u00e7meniz gerekebilir.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Bir eylem se\u00e7tiniz, fakat bireysel alanlar \u00fczerinde hi\u00e7bir de\u011fi\u015fiklik yapmad\u0131n\u0131z. Muhtemelen Kaydet d\u00fc\u011fmesi yerine Git d\u00fc\u011fmesini ar\u0131yorsunuz.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Bir eylem se\u00e7tiniz, fakat hen\u00fcz bireysel alanlara de\u011fi\u015fikliklerinizi kaydetmediniz. Kaydetmek i\u00e7in l\u00fctfen TAMAM d\u00fc\u011fmesine t\u0131klay\u0131n. Eylemi yeniden \u00e7al\u0131\u015ft\u0131rman\u0131z gerekecek.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Bireysel d\u00fczenlenebilir alanlarda kaydedilmemi\u015f de\u011fi\u015fiklikleriniz var. E\u011fer bir eylem \u00e7al\u0131\u015ft\u0131r\u0131rsan\u0131z, kaydedilmemi\u015f de\u011fi\u015fiklikleriniz kaybolacakt\u0131r.", 
    "You must provide a learner name.": "Bir \u00f6\u011frenci ismi belirtmelisiniz.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Bu g\u00f6rev i\u00e7in cevab\u0131n\u0131 g\u00f6ndermek \u00fczeresin. Cevab\u0131n\u0131 g\u00f6nderdikten sonra, cevab\u0131 de\u011fi\u015ftiremez veya yeni bir cevap ekleyemezsin.", 
    "Your file ": "Dosyan\u0131z", 
    "active proctored exams": "etkinle\u015ftirilmi\u015f g\u00f6zetmenli s\u0131navlar", 
    "courses with active proctored exams": "g\u00f6zetmenli s\u0131navlara sahip dersler", 
    "internally reviewed": "dahili olarak g\u00f6zden ge\u00e7irildi", 
    "one letter Friday\u0004F": "C", 
    "one letter Monday\u0004M": "P", 
    "one letter Saturday\u0004S": "C", 
    "one letter Sunday\u0004S": "P", 
    "one letter Thursday\u0004T": "P", 
    "one letter Tuesday\u0004T": "S", 
    "one letter Wednesday\u0004W": "\u00c7", 
    "pending": "beklemede", 
    "practice": "al\u0131\u015ft\u0131rma", 
    "proctored": "g\u00f6zetmenli", 
    "satisfactory": "yeterli", 
    "timed": "zamanlanm\u0131\u015f", 
    "unsatisfactory": "yetersiz", 
    "you have less than a minute remaining": "Bir dakikadan az zaman\u0131n\u0131z kald\u0131", 
    "you have {remaining_time} remaining": "{remaining_time} dakika zaman\u0131n\u0131z kald\u0131", 
    "your course": "dersiniz", 
    "{num_of_hours} hour": "{num_of_hours} saat", 
    "{num_of_hours} hours": "{num_of_hours} saat", 
    "{num_of_minutes} minute": "{num_of_minutes} dakika", 
    "{num_of_minutes} minutes": "{num_of_minutes} dakika"
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
    "DATETIME_FORMAT": "d F Y H:i", 
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S", 
      "%d/%m/%Y %H:%M:%S.%f", 
      "%d/%m/%Y %H:%M", 
      "%d/%m/%Y", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d"
    ], 
    "DATE_FORMAT": "d F Y", 
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y", 
      "%d/%m/%y", 
      "%y-%m-%d", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "d F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d M Y H:i", 
    "SHORT_DATE_FORMAT": "d M Y", 
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

