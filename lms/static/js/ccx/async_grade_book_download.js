var edx = edx || {};

(function($, _, Backbone, gettext) {
  'use strict';
  edx.ccx = edx.ccx || {};
  edx.ccx.grade_book_download = edx.ccx.grade_book_download || {};

  edx.ccx.grade_book_download.GradeBookDownloadView = Backbone.View.extend({
    events: {
      "click a#ccx-calculate-grades-csv" : "asyncPrepareGradeBook"
    },
    initialize: function() {
      // set interval to fetch list of files that are ready for download.
      var self = this;
      this.clearMessageBoxes();
      this.showListOfDownloadedGradeBooks();
    },
    render: function () {
      return this;
    },
    reloadListOfDownloadedGradeBooks: function() {
      // refresh list of grade books, ready for download.
      var self = this;
      this.clearMessageBoxes();
      // Fetch interval for grade book download request 40 sec.
      var POLL_INTERVAL = 30000;
      this.timer = setInterval(function() {
        self.showListOfDownloadedGradeBooks();
      }, POLL_INTERVAL);
    },
    showListOfDownloadedGradeBooks: function() {
      // Get list of grade book files that are ready for download
      var alreadyDownloadedUrl = $("#ccx_report-downloads-table").data('endpoint');
      var self = this;
      $.ajax({
        dataType: 'json',
        url: alreadyDownloadedUrl
      }).done(function(data) {
        if (data.downloads.length > 0) {
          self.renderListOfReadyDownload(data.downloads);
           if (!_.isUndefined(this.timer)) {
              clearInterval(this.timer);
           }
        } else {
          var $successResponseHolder = $('#ccx-gradebook-request-response');
          $successResponseHolder.text(gettext(
            "No reports ready for download"
          ));
          $successResponseHolder.show();
        }
      }).fail(function() {
        var $failureResponseHolder = $('#ccx-gradebook-request-response-error');
        $failureResponseHolder.text(
          gettext("Error with fetching list of grade books. Please try again.")
        );
        $failureResponseHolder.show();
      });
    },
    clearMessageBoxes: function() {
      // clear status bar for error
      var $failureResponseHolder = $('#ccx-gradebook-request-response-error');
      $failureResponseHolder.hide();
    },
    asyncPrepareGradeBook: function (event) {
      // Prepare grade book asynchronously for download
      var self = this;
      var asyncDownloadUrl = $(event.target).data('endpoint');
      $.ajax({
        dataType: 'json',
        url: asyncDownloadUrl
      }).done(function(data) {
        var $successResponseHolder = $('#ccx-gradebook-request-response');
        $successResponseHolder.text(data['status']);
        $successResponseHolder.show();
        self.reloadListOfDownloadedGradeBooks();
      }).fail(function() {
        var $failureResponseHolder = $('#ccx-gradebook-request-response-error');
        $failureResponseHolder.text(
          gettext("Error generating grade book. Please try again.")
        );
        $failureResponseHolder.show();
      });
    },
    renderListOfReadyDownload: function(gradeBookDownloadsData) {
      // Renders list of files ready to download.
      var $tablePlaceHolder, columns, grid, options;
      var $fileGridHolder = $("#ccx_report-downloads-table");
      $fileGridHolder.empty();
      options = {
        enableCellNavigation: true,
        enableColumnReorder: false,
        rowHeight: 30,
        forceFitColumns: true
      };
      columns = [
        {
          id: 'link',
          field: 'link',
          name: gettext('File Name'),
          toolTip: gettext("Links are generated on demand and expire within 5 minutes due to the sensitive nature of student information."),
          sortable: false,
          minWidth: 900,
          cssClass: "file-download-link",
          formatter: function(row, cell, value, columnDef, dataContext) {
            return '<a target="_blank" href="' + dataContext['url'] + '">' + dataContext['name'] + '</a>';
          }
        }
      ];
      $tablePlaceHolder = $('<div/>', {
        "class": 'slickgrid',
        "style": 'min-height: 60px;'
      });
      $fileGridHolder.append($tablePlaceHolder);
      grid = new Slick.Grid($tablePlaceHolder, gradeBookDownloadsData, columns, options);
      grid.autosizeColumns();
    }
  });

})(jQuery, _, Backbone, gettext);
