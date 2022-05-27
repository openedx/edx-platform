

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = 0;
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
      "%(cnt)s dan %(sel)s tanlandi"
    ],
    "6 a.m.": "6 t.o.",
    "6 p.m.": "6 t.k.",
    "April": "Aprel",
    "August": "Avgust",
    "Available %s": "Mavjud %s",
    "Cancel": "Bekor qilish",
    "Choose": "Tanlash",
    "Choose a Date": "Sanani tanlang",
    "Choose a Time": "Vaqtni tanlang",
    "Choose a time": "Vaqtni tanlang",
    "Choose all": "Barchasini tanlash",
    "Chosen %s": "Tanlangan %s",
    "Click to choose all %s at once.": "Barcha %s larni birdan tanlash uchun bosing.",
    "Click to remove all chosen %s at once.": "Barcha tanlangan %s larni birdan o'chirib tashlash uchun bosing.",
    "December": "Dekabr",
    "February": "Fevral",
    "Filter": "Filtrlash",
    "Hide": "Yashirish",
    "January": "Yanvar",
    "July": "Iyul",
    "June": "Iyun",
    "March": "Mart",
    "May": "May",
    "Midnight": "Yarim tun",
    "Noon": "Kun o'rtasi",
    "Note: You are %s hour ahead of server time.": [
      "Eslatma: Siz server vaqtidan %s soat oldindasiz."
    ],
    "Note: You are %s hour behind server time.": [
      "Eslatma: Siz server vaqtidan %s soat orqadasiz."
    ],
    "November": "Noyabr",
    "Now": "Hozir",
    "October": "Oktabr",
    "Remove": "O'chirish",
    "Remove all": "Barchasini o'chirish",
    "September": "Sentabr",
    "Show": "Ko'rsatish",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Bu mavjud %s ro'yxati. Siz ulardan ba'zilarini quyidagi maydonchada belgilab, so'ng ikkala maydonlar orasidagi \"Tanlash\" ko'rsatkichiga bosish orqali tanlashingiz mumkin.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Bu tanlangan %s ro'yxati. Siz ulardan ba'zilarini quyidagi maydonchada belgilab, so'ng ikkala maydonlar orasidagi \"O'chirish\" ko'rsatkichiga bosish orqali o'chirishingiz mumkin.",
    "Today": "Bugun",
    "Tomorrow": "Ertaga",
    "Type into this box to filter down the list of available %s.": "Mavjud bo'lgan %s larni ro'yxatini filtrlash uchun ushbu maydonchaga kiriting.",
    "Yesterday": "Kecha",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Siz harakatni tanladingiz va alohida maydonlarda hech qanday o'zgartirishlar kiritmadingiz. Ehtimol siz Saqlash tugmasini emas, balki O'tish tugmasini qidirmoqdasiz.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Siz harakatni tanladingiz, lekin hali ham o'zgartirishlaringizni alohida maydonlarga saqlamadingiz. Iltimos saqlash uchun OK ni bosing. Harakatni qayta ishga tushurishingiz kerak bo'ladi.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Siz alohida tahrirlash mumkin bo'lgan maydonlarda saqlanmagan o\u2018zgarishlaringiz mavjud. Agar siz harakatni ishga tushirsangiz, saqlanmagan o'zgarishlaringiz yo'qotiladi.",
    "one letter Friday\u0004F": "F",
    "one letter Monday\u0004M": "M",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "S",
    "one letter Thursday\u0004T": "T",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "W"
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
    "DATETIME_FORMAT": "j-E, Y-\\y\\i\\l G:i",
    "DATETIME_INPUT_FORMATS": [
      "%d.%m.%Y %H:%M:%S",
      "%d.%m.%Y %H:%M:%S.%f",
      "%d.%m.%Y %H:%M",
      "%d-%B, %Y-yil %H:%M:%S",
      "%d-%B, %Y-yil %H:%M:%S.%f",
      "%d-%B, %Y-yil %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j-E, Y-\\y\\i\\l",
    "DATE_INPUT_FORMATS": [
      "%d.%m.%Y",
      "%d-%B, %Y-yil",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j-E",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d.m.Y H:i",
    "SHORT_DATE_FORMAT": "d.m.Y",
    "THOUSAND_SEPARATOR": "\u00a0",
    "TIME_FORMAT": "G:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F Y-\\y\\i\\l"
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

