

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=0;
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "\n        No, I want to continue working.\n      ": "\nTidak, saya ingin lanjut bekerja.", 
    "\n      After you submit your exam, your exam will be graded.\n    ": "\nSetelah Anda mengirimkan jawaban ujian,  jawaban Anda akan dinilai.", 
    " and {num_of_minutes} minutes": "dan {num_of_minutes} menit", 
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s dari %(cnt)s terpilih"
    ], 
    "(required):": "(wajib diisi):", 
    "6 a.m.": "6 pagi", 
    "6 p.m.": "18.00", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "Setelah Anda mengunggah berkas-berkas baru, semua berkas-berkas yang telah Anda unggah sebelumnya akan tertimpa. Lanjutkan?", 
    "All Unreviewed": "Semua yang belum diulas", 
    "April": "April", 
    "Assessment": "Penilaian", 
    "Assessments": "Penilaian", 
    "August": "Agustus", 
    "Available %s": "%s yang tersedia", 
    "Back to Full List": "Kembali ke Daftar Penuh", 
    "Block view is unavailable": "Tampilan blok tidak tersedia", 
    "Cancel": "Batal", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "Perubahan pada langkah-langkah yang tidak terpilih sebagai bagian penugasan tidak akan disimpan.", 
    "Choose": "Pilih", 
    "Choose a Date": "Pilih Tanggal", 
    "Choose a Time": "Pilih Waktu", 
    "Choose a time": "Pilih waktu", 
    "Choose all": "Pilih semua", 
    "Chosen %s": "%s terpilih", 
    "Click to choose all %s at once.": "Pilih untuk memilih seluruh %s sekaligus.", 
    "Click to remove all chosen %s at once.": "Klik untuk menghapus semua pilihan %s sekaligus.", 
    "Continue to my practice exam": "Lanjut ke ujian sesi latihan", 
    "Could not retrieve download url.": "Gagal mencapai url unduhan.", 
    "Could not retrieve upload url.": "Gagal mencapai url unggahan.", 
    "Couldn't Save This Assignment": "Gagal Menyimpan Tugas Ini", 
    "Course Id": "Id pelatihan", 
    "Created": "Telah dibuat", 
    "Criterion Added": "Kriteria telah ditambahkan", 
    "Criterion Deleted": "Kriteria telah dihapus", 
    "December": "Desember", 
    "Declined": "Ditolak", 
    "Describe ": "Deskripsikan", 
    "Do you want to upload your file before submitting?": "Apakah Anda ingin mengunggah berkas Anda sebelum mengirimkan?", 
    "Download Software Clicked": "Unduh software yang telah dipilih", 
    "Error": "Kesalahan", 
    "Error getting the number of ungraded responses": "Tidak dapat menampilkan jumlah tanggapan yang belum dinilai.", 
    "Failed Proctoring": "Gagal dalam proses proktoring", 
    "February": "Februari", 
    "Feedback available for selection.": "Umpan balik tersedia untuk pilihan Anda.", 
    "File size must be 10MB or less.": "Ukuran berkas harus 10MB atau kurang.", 
    "File type is not allowed.": "Jenis berkas ini tidak diperkenankan", 
    "File types can not be empty.": "Jenis berkas tidak dapat dikosongkan.", 
    "Filter": "Filter", 
    "Final Grade Received": "Nilai Akhir Diterima", 
    "Hide": "Ciutkan", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "Jika Anda meninggalkan halaman ini tanpa menyimpan atau mengirim tanggapan Anda, Anda akan kehilangan semua pekerjaan yang Anda buat pada tanggapan Anda.", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "Jika Anda meninggalkan halaman ini tanpa mengirimkan penilaian sebaya Anda, Anda akan kehilangan pekerjaan yang Anda lakukan.", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "Jika Anda meninggalkan halaman tanpa mengirimkan hasil penilaian mandiri, Anda akan kehilangan pekerjaan Anda barusan.", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "Jika Anda meninggalkan halaman tanpa mengirimkan hasil penilaian staf, Anda akan kehilangan pekerjaan Anda barusan.", 
    "January": "Januari", 
    "July": "Juli", 
    "June": "Juni", 
    "List of Open Assessments is unavailable": "Daftar Penilaian Terbuka tidak tersedia", 
    "March": "Maret", 
    "May": "Mei", 
    "Midnight": "Tengah malam", 
    "Must be a Staff User to Perform this request.": "Harus menjadi Staf untuk melakukan permintaan ini.", 
    "Noon": "Siang", 
    "Not Selected": "Tak Terpilih", 
    "Note: You are %s hour ahead of server time.": [
      "Catatan: Waktu Anda lebih cepat %s jam dibandingkan waktu server."
    ], 
    "Note: You are %s hour behind server time.": [
      "Catatan: Waktu Anda lebih lambat %s jam dibandingkan waktu server."
    ], 
    "November": "November", 
    "Now": "Sekarang", 
    "October": "Oktober", 
    "One or more rescheduling tasks failed.": "Salah satu tugas penjadwalan telah gagal.", 
    "Option Deleted": "Opsi Dihapus", 
    "Passed Proctoring": "Lulus proses proktoring", 
    "Peer": "Rekan", 
    "Pending Session Review": "Ulasan sesi yang tertunda", 
    "Please correct the outlined fields.": "Silakan perbaiki bidang-bidang bergaris tepi.", 
    "Please wait": "Mohon tunggu", 
    "Practice Exam Completed": "Sesi Latihan telah diselesaikan", 
    "Practice Exam Failed": "Gagal dalam ujian sesi latihan", 
    "Proctored Option Available": "Pilihan proktor tersedia", 
    "Proctored Option No Longer Available": "Pilihan proktor tidak tersedia lagi", 
    "Ready To Start": "Siap memulai", 
    "Ready To Submit": "Siap untuk mengirimkan", 
    "Remove": "Hapus", 
    "Remove all": "Hapus semua", 
    "Review Policy Exception": "Tinjau kebijakan pengecualian", 
    "Saving...": "Sedang menyimpan ...", 
    "Second Review Required": "Diperlukan ulasan kedua", 
    "Self": "Sendiri", 
    "September": "September", 
    "Server error.": "Server error.", 
    "Show": "Bentangkan", 
    "Staff": "Staf", 
    "Started": "Dimulai", 
    "Status of Your Response": "Status respon Anda", 
    "Taking As Open Exam": "Mengambil ujian terbuka", 
    "The display of ungraded and checked out responses could not be loaded.": "Tampilan tanggapan yang diminta tidak dapat dimuat.", 
    "The following file types are not allowed: ": "Jenis berkas berikut tidak diperkenankan:", 
    "The server could not be contacted.": "Server tidak dapat dihubungi.", 
    "The staff assessment form could not be loaded.": "Form penilaian staf tidak dapat dimuat.", 
    "The submission could not be removed from the grading pool.": "Pengajuan tidak bisa dihapus dari kolom peringkat.", 
    "This assessment could not be submitted.": "Penilaian ini tidak dapat dikirimkan.", 
    "This exam has a time limit associated with it.": "Ujian ini memiliki batas waktu yang berkaitan dengan hal ini.", 
    "This feedback could not be submitted.": "Umpan balik ini tidak dapat dikirimkan.", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Berikut adalah daftar %s yang tersedia. Anda dapat memilih satu atau lebih dengan memilihnya pada kotak di bawah, lalu mengeklik tanda panah \"Pilih\" di antara kedua kotak.", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Berikut adalah daftar %s yang terpilih. Anda dapat menghapus satu atau lebih dengan memilihnya pada kotak di bawah, lalu mengeklik tanda panah \"Hapus\" di antara kedua kotak.", 
    "This problem could not be saved.": "Masalah ini tidak dapat disimpan.", 
    "This problem has already been released. Any changes will apply only to future assessments.": "Masalah ini telah dilepas. Perubahan yang terjadi hanya akan diterapkan pada penilaian mendatang.", 
    "This response could not be saved.": "Respon ini tidak dapat disimpan.", 
    "This response could not be submitted.": "Respon ini tidak dapat dikirimkan.", 
    "This response has been saved but not submitted.": "Respon ini akan disimpan namun tidak dikirimkan.", 
    "This response has not been saved.": "Respon belum disimpan.", 
    "This section could not be loaded.": "Bagian ini tidak dapat dimuat.", 
    "Thumbnail view of ": "Tampilan thumbnail dari", 
    "Timed Out": "Waktu habis", 
    "To pass this exam, you must complete the problems in the time allowed.": "Untuk lulus ujian, Anda harus menyelesaikan masalah dalam waktu yang telah ditentukan.", 
    "Today": "Hari ini", 
    "Tomorrow": "Besok", 
    "Total Responses": "Tanggapan Total", 
    "Training": "Pelatihan", 
    "Type into this box to filter down the list of available %s.": "Ketik pada kotak ini untuk menyaring daftar %s yang tersedia.", 
    "Unable to load": "Tidak dapat memuat", 
    "Unexpected server error.": "Kesalahan server yang tidak terduga.", 
    "Ungraded Practice Exam": "Ujian sesi latihan yang tidak masuk dalam penilaian", 
    "Unit Name": "Nama Unit", 
    "Units": "Unit", 
    "Unnamed Option": "Opsi Tanpa Judul", 
    "Waiting": "Menunggu", 
    "Warning": "Peringatan", 
    "Yesterday": "Kemarin", 
    "You can upload files with these file types: ": "Anda dapat mengunggah berkas dengan jenis sebagai berikut:", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "Anda telah menambahkan kriteria. Anda perlu memiliki satu opsi untuk pilihan dalam langkah Pelatihan Pembelajar. Untuk melakukannya, klik tab Setelan.", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "Anda telah menghapus satu kriteria. Kriteria telah dihapus dari contoh tanggapan pada langkah Pelatihan Pembelajar.", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "Anda telah menghapus semua opsi untuk kriteria ini. Kriteria telah dihapus dari contoh tanggapan pada langkah Pelatihan Pembelajar.", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "Anda telah menghapus sebuah opsi. Opsi tersebut telah dihapus dari kriteria pada contoh tanggapan pada langkah Pelatihan Pembelajar. Anda mungkin perlu memilih opsi baru untuk kriteria tersebut.", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Anda telah memilih sebuah aksi, tetapi belum mengubah bidang apapun. Kemungkinan Anda mencari tombol Buka dan bukan tombol Simpan.", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Anda telah memilih sebuah aksi, tetapi belum menyimpan perubahan ke bidang yang ada. Klik OK untuk menyimpan perubahan ini. Anda akan perlu mengulangi aksi tersebut kembali.", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Beberapa perubahan bidang yang Anda lakukan belum tersimpan. Perubahan yang telah dilakukan akan hilang.", 
    "You must provide a learner name.": "Anda harus memasukkan nama pembelajar.", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "Anda akan mengirimkan tanggapan Anda untuk tugas ini. Setelah Anda mengirimkan tanggapan ini, Anda tidak dapat mengubah atau menyampaikan tanggapan baru.", 
    "active proctored exams": "Ujian proktor aktif", 
    "could not determine the course_id": "tidak dapat menentukan course_id", 
    "courses with active proctored exams": "Pelatihan dengan ujian proktor aktif", 
    "internally reviewed": "Telah diulas secara internal", 
    "one letter Friday\u0004F": "J", 
    "one letter Monday\u0004M": "S", 
    "one letter Saturday\u0004S": "S", 
    "one letter Sunday\u0004S": "M", 
    "one letter Thursday\u0004T": "K", 
    "one letter Tuesday\u0004T": "S", 
    "one letter Wednesday\u0004W": "R", 
    "practice": "Latihan", 
    "proctored": "Proktor", 
    "satisfactory": "Memuaskan", 
    "unsatisfactory": "Tidak memuaskan", 
    "you have less than a minute remaining": "Anda hanya memiliki sisa waktu kurang dari satu menit.", 
    "you have {remaining_time} remaining": "Anda memiliki {remaining_time} tersisa", 
    "your course": "Pelatihan anda", 
    "{num_of_minutes} minute": "{num_of_minutes} menit"
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
    "DATETIME_FORMAT": "j N Y, G.i", 
    "DATETIME_INPUT_FORMATS": [
      "%d-%m-%Y %H.%M.%S", 
      "%d-%m-%Y %H.%M.%S.%f", 
      "%d-%m-%Y %H.%M", 
      "%d-%m-%Y", 
      "%d-%m-%y %H.%M.%S", 
      "%d-%m-%y %H.%M.%S.%f", 
      "%d-%m-%y %H.%M", 
      "%d-%m-%y", 
      "%m/%d/%y %H.%M.%S", 
      "%m/%d/%y %H.%M.%S.%f", 
      "%m/%d/%y %H.%M", 
      "%m/%d/%y", 
      "%m/%d/%Y %H.%M.%S", 
      "%m/%d/%Y %H.%M.%S.%f", 
      "%m/%d/%Y %H.%M", 
      "%m/%d/%Y", 
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d"
    ], 
    "DATE_FORMAT": "j N Y", 
    "DATE_INPUT_FORMATS": [
      "%d-%m-%y", 
      "%d/%m/%y", 
      "%d-%m-%Y", 
      "%d/%m/%Y", 
      "%d %b %Y", 
      "%d %B %Y", 
      "%Y-%m-%d"
    ], 
    "DECIMAL_SEPARATOR": ",", 
    "FIRST_DAY_OF_WEEK": "1", 
    "MONTH_DAY_FORMAT": "j F", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "d-m-Y G.i", 
    "SHORT_DATE_FORMAT": "d-m-Y", 
    "THOUSAND_SEPARATOR": ".", 
    "TIME_FORMAT": "G.i", 
    "TIME_INPUT_FORMATS": [
      "%H.%M.%S", 
      "%H.%M", 
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

