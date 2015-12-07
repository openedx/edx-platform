var edx = edx || {};

(function($, _, Backbone, gettext) {
  'use strict';
  edx.ccx = edx.ccx || {};
  edx.ccx.grade_book_download = edx.ccx.grade_book_download || {};

  edx.ccx.grade_book_download.GradeBookDownloadView = Backbone.View.extend({
    events: {
      "click a#ccx-calculate-grades-csv" : "asyncDownloadGradeBook"
    },
    initialize: function() {
      this.clearMessageBoxes();
      this.showListOfDownloadedGradeBooks();
    },
    render: function () {
      this.showListOfDownloadedGradeBooks();
      return this;
    },
    showListOfDownloadedGradeBooks: function() {
      var alreadyDownloadedUrl = $("#ccx_report-downloads-table").data('endpoint');
      var self = this;
      $.ajax({
        dataType: 'json',
        url: alreadyDownloadedUrl
      }).done(function(data) {
        if (data.downloads.length > 0) {
          self.renderListOfReadyDownload(data.downloads);
        } else {
          var $successResponseHolder = $('.msg-confirm');
          $successResponseHolder.text(gettext(
            "No reports ready for download"
          ));
        }
      }).fail(function() {
        var $failureResponseHolder = $('.msg-error');
        $failureResponseHolder.text(
          gettext("Error with fetching list of grade books. Please try again.")
        );
        $failureResponseHolder.css({"display":"block"})
      });
    },
    clearMessageBoxes: function() {
      var $successResponseHolder = $('.msg-confirm');
      var $failureResponseHolder = $('.msg-error');
      $successResponseHolder.text("");
      $failureResponseHolder.text("");
    },
    asyncDownloadGradeBook: function (event) {
      this.clearMessageBoxes();
      var asyncDownloadUrl = $(event.target).data('endpoint');
      $.ajax({
        dataType: 'json',
        url: asyncDownloadUrl
      }).done(function(data) {
        var $successResponseHolder = $('.msg-confirm');
        $successResponseHolder.text(data['status']);
      }).fail(function() {
        var $failureResponseHolder = $('.msg-error');
        $failureResponseHolder.text(
          gettext("Error generating grade book. Please try again.")
        );
      });
    },
    renderListOfReadyDownload: function(report_downloads_data) {
      var $table_placeholder, columns, grid, options,
        _this = this;
      var $fileGridHolder = $("#ccx_report-downloads-table");
      $fileGridHolder.html("");
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
          minWidth: 1000,
          cssClass: "file-download-link",
          formatter: function(row, cell, value, columnDef, dataContext) {
            return '<a target="_blank" href="' + dataContext['url'] + '">' + dataContext['name'] + '</a>';
          }
        }
      ];
      $table_placeholder = $('<div/>', {
        "class": 'slickgrid'
      });
      $fileGridHolder.append($table_placeholder);
      grid = new Slick.Grid($table_placeholder, report_downloads_data, columns, options);
      grid.onClick.subscribe(function(event) {
        var report_url;
        report_url = event.target.href;
        if (report_url) {
          return Logger.log('edx.instructor.report.downloaded', {
            report_url: report_url
          });
        }
      });
      return grid.autosizeColumns();
    }
  });

})(jQuery, _, Backbone, gettext);
