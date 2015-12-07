var define = window.define || RequireJS.define;  // jshint ignore:line

define("async_grade_book_download",
  [
    'backbone',
    'underscore',
    'gettext',
    'text!templates/ccx/grade_book_download.underscore'
  ],
  function (Backbone, _, gettext, gradeBookDownloadTemplate) {
    'use strict';
    var GradeBookDownloadView = Backbone.View.extend({

      events: {
        "click a#ccx-calculate-grades-csv" : "asyncPrepareGradeBook"
      },

      initialize: function(options) {
        // set interval to fetch list of files that are ready for download.
        this.gradeBookPrepareUrl = options.gradeBookPrepareUrl;
        this.listPreparedGradeBookUrl = options.listPreparedGradeBookUrl;
        this.showErrorMessage = false;
        this.showSuccessMessage = false;
        this.showReadyGradeBooks();
      },

      render: function () {
        this.$el.html(_.template(gradeBookDownloadTemplate) ({
          showErrorMessage: this.showErrorMessage,
          showSuccessMessage: this.showSuccessMessage
        }));
        return this;
      },

      reloadDownloadList: function() {
        // refresh list of grade books, ready for download.
        var self = this;
        // Fetch interval for grade book download request 20 sec.
        var POLL_INTERVAL = 20000;
        this.timer = setInterval(function() {
          self.showReadyGradeBooks();
        }, POLL_INTERVAL);
      },

      showReadyGradeBooks: function() {
        // Get list of grade book files that are ready for download
        var self = this;
        $.ajax({
          dataType: 'json',
          url: self.listPreparedGradeBookUrl
        }).done(function(data) {
          if (data.downloads.length > 0) {
            self.renderListOfReadyDownload(data.downloads);
             if (!_.isUndefined(self.timer)) {
                clearInterval(self.timer);
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

      asyncPrepareGradeBook: function (event) {
        event.preventDefault();
        // Prepare grade book asynchronously for download
        var self = this;
        $.ajax({
          dataType: 'json',
          url: self.gradeBookPrepareUrl
        }).done(function(data) {
          self.showErrorMessage = false;
          self.showSuccessMessage = true;
          self.render();
          var $successResponseHolder = $('#ccx-gradebook-request-response');
          $successResponseHolder.text(data.status);
          $successResponseHolder.show();
          self.reloadDownloadList();
        }).fail(function() {
          self.showErrorMessage = true;
          self.showSuccessMessage = false;
          self.render();
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
            toolTip: gettext("Links are generated on demand and expire within" +
              " 5 minutes due to the sensitive nature of student information."),
            sortable: false,
            minWidth: 900,
            cssClass: "file-download-link",
            formatter: function(row, cell, value, columnDef, dataContext) {
              return '<a target="_blank" href="' + dataContext.url + '">' + dataContext.name + '</a>';
            }
          }
        ];
        $tablePlaceHolder = $('<div/>', {
          "class": 'slickgrid',
          "style": 'min-height: 60px;'
        });
        $fileGridHolder.append($tablePlaceHolder);

        /* globals Slick */
        grid = new Slick.Grid($tablePlaceHolder, gradeBookDownloadsData, columns, options);
        grid.autosizeColumns();
      }
    });

    return {
      "GradeBookDownloadView": GradeBookDownloadView
    };
  }
);

