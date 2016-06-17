/**
 * Data Download Section
 */
(function(Slick, DataDownload_Certificate) {
    'use strict';

    var DataDownload, PendingInstructorTasks, ReportDownloads, std_ajax_err;

    std_ajax_err = function() {
        return window.InstructorDashboard.util.std_ajax_err.apply(this, arguments);
    };

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    ReportDownloads = function() {
        return window.InstructorDashboard.util.ReportDownloads;
    };

    this.DataDownload_Certificate = (function() {

        function DataDownload_Certificate($container) {
            var _this = this;
            this.$container = $container;
            this.$list_issued_certificate_table_btn = this.$container.find("input[name='issued-certificates-list']");
            this.$list_issued_certificate_csv_btn = this.$container.find("input[name='issued-certificates-csv']");
            this.$certificate_display_table = this.$container.find('.certificate-data-display-table');
            this.$certificates_request_response_error = this.$container.find('.issued-certificates-error.request-response-error');  // jshint ignore:line
            this.$list_issued_certificate_table_btn.click(function() {
                var url;
                url = _this.$list_issued_certificate_table_btn.data('endpoint');
                _this.clear_ui();
                _this.$certificate_display_table.text(gettext('Loading data...'));
                return $.ajax({
                    type: 'POST',
                    url: url,
                    error: function() {
                        _this.clear_ui();
                        _this.$certificates_request_response_error.text(
                            gettext("Error getting issued certificates list.")
                        );
                        return $(".issued_certificates .issued-certificates-error.msg-error").css({
                            "display": "block"
                        });
                    },
                    success: function(data) {
                        var $table_placeholder, columns, feature, grid_data, options;
                        _this.clear_ui();
                        options = {
                            enableCellNavigation: true,
                            enableColumnReorder: false,
                            forceFitColumns: true,
                            rowHeight: 35
                        };
                        columns = (function() {
                            var _i, _len, _ref, _results;
                            _ref = data.queried_features;
                            _results = [];
                            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                                feature = _ref[_i];
                                _results.push({
                                    id: feature,
                                    field: feature,
                                    name: data.feature_names[feature]
                                });
                            }
                            return _results;
                        })();
                        grid_data = data.certificates;
                        $table_placeholder = $('<div/>', {
                            "class": 'slickgrid'
                        });
                        _this.$certificate_display_table.append($table_placeholder);
                        return new Slick.Grid($table_placeholder, grid_data, columns, options);
                    }
                });
            });
            this.$list_issued_certificate_csv_btn.click(function() {
                var url;
                _this.clear_ui();
                url = _this.$list_issued_certificate_csv_btn.data('endpoint');
                location.href = url + '?csv=true';
            });
        }

        DataDownload_Certificate.prototype.clear_ui = function() {
            this.$certificate_display_table.empty();
            this.$certificates_request_response_error.empty();
            return $(".issued-certificates-error.msg-error").css({
                "display": "none"
            });
        };

        return DataDownload_Certificate;

    })();

    DataDownload = (function() {

        function DataDownload($section) {
            var _this = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            new DataDownload_Certificate(this.$section.find('.issued_certificates'));  // jshint ignore:line
            this.$list_studs_btn = this.$section.find("input[name='list-profiles']");
            this.$list_studs_csv_btn = this.$section.find("input[name='list-profiles-csv']");
            this.$list_proctored_exam_results_csv_btn = this.$section.find("input[name='proctored-exam-results-report']");  // jshint ignore:line
            this.$survey_results_csv_btn = this.$section.find("input[name='survey-results-report']");
            this.$list_may_enroll_csv_btn = this.$section.find("input[name='list-may-enroll-csv']");
            this.$list_problem_responses_csv_input = this.$section.find("input[name='problem-location']");
            this.$list_problem_responses_csv_btn = this.$section.find("input[name='list-problem-responses-csv']");
            this.$list_anon_btn = this.$section.find("input[name='list-anon-ids']");
            this.$grade_config_btn = this.$section.find("input[name='dump-gradeconf']");
            this.$calculate_grades_csv_btn = this.$section.find("input[name='calculate-grades-csv']");
            this.$problem_grade_report_csv_btn = this.$section.find("input[name='problem-grade-report']");
            this.$async_report_btn = this.$section.find("input[class='async-report-btn']");
            this.$download = this.$section.find('.data-download-container');
            this.$download_display_text = this.$download.find('.data-display-text');
            this.$download_request_response_error = this.$download.find('.request-response-error');
            this.$reports = this.$section.find('.reports-download-container');
            this.$download_display_table = this.$reports.find('.profile-data-display-table');
            this.$reports_request_response = this.$reports.find('.request-response');
            this.$reports_request_response_error = this.$reports.find('.request-response-error');
            this.report_downloads = new (ReportDownloads())(this.$section);
            this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            this.clear_display();
            this.$list_anon_btn.click(function() {
                var url;
                url = _this.$list_anon_btn.data('endpoint');
                location.href = url;
            });
            this.$list_proctored_exam_results_csv_btn.click(function() {
                var url;
                url = _this.$list_proctored_exam_results_csv_btn.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: function() {
                        _this.clear_display();
                        _this.$reports_request_response_error.text(
                            gettext("Error generating proctored exam results. Please try again.")
                        );
                        $(".msg-error").css({
                            "display": "block"
                        });
                    },
                    success: function(data) {
                        _this.clear_display();
                        _this.$reports_request_response.text(data.status);
                        $(".msg-confirm").css({
                            "display": "block"
                        });
                    }
                });
            });
            this.$survey_results_csv_btn.click(function() {
                var url;
                url = _this.$survey_results_csv_btn.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: function() {
                        _this.clear_display();
                        _this.$reports_request_response_error.text(
                            gettext("Error generating survey results. Please try again.")
                        );
                        $(".msg-error").css({
                            "display": "block"
                        });
                    },
                    success: function(data) {
                        _this.clear_display();
                        _this.$reports_request_response.text(data.status);
                        $(".msg-confirm").css({
                            "display": "block"
                        });
                    }
                });
            });
            this.$list_studs_csv_btn.click(function() {
                var url;
                _this.clear_display();
                url = _this.$list_studs_csv_btn.data('endpoint');
                url += '/csv';
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: function() {
                        _this.$reports_request_response_error.text(
                            gettext("Error generating student profile information. Please try again.")
                        );
                        $(".msg-error").css({
                            "display": "block"
                        });
                    },
                    success: function(data) {
                        _this.$reports_request_response.text(data.status);
                        $(".msg-confirm").css({
                            "display": "block"
                        });
                    }
                });
            });
            this.$list_studs_btn.click(function() {
                var url;
                url = _this.$list_studs_btn.data('endpoint');
                _this.clear_display();
                _this.$download_display_table.text(gettext('Loading'));
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: function() {
                        _this.clear_display();
                        _this.$download_request_response_error.text(
                            gettext("Error getting student list.")
                        );
                    },
                    success: function(data) {
                        var $table_placeholder, columns, feature, grid, grid_data, options;
                        _this.clear_display();
                        options = {
                            enableCellNavigation: true,
                            enableColumnReorder: false,
                            forceFitColumns: true,
                            rowHeight: 35
                        };
                        columns = (function() {
                            var _i, _len, _ref, _results;
                            _ref = data.queried_features;
                            _results = [];
                            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                                feature = _ref[_i];
                                _results.push({
                                    id: feature,
                                    field: feature,
                                    name: data.feature_names[feature]
                                });
                            }
                            return _results;
                        })();
                        grid_data = data.students;
                        $table_placeholder = $('<div/>', {
                            "class": 'slickgrid'
                        });
                        _this.$download_display_table.append($table_placeholder);
                        grid = new Slick.Grid($table_placeholder, grid_data, columns, options);
                    }
                });
            });
            this.$list_problem_responses_csv_btn.click(function() {
                var url;
                _this.clear_display();
                url = _this.$list_problem_responses_csv_btn.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    data: {
                        problem_location: _this.$list_problem_responses_csv_input.val()
                    },
                    error: function(error) {
                        _this.$reports_request_response_error.text(
                            JSON.parse(error.responseText)
                        );
                        $(".msg-error").css({
                            "display": "block"
                        });
                    },
                    success: function(data) {
                        _this.$reports_request_response.text(data.status);
                        $(".msg-confirm").css({
                            "display": "block"
                        });
                    }
                });
            });
            this.$list_may_enroll_csv_btn.click(function() {
                var url;
                _this.clear_display();
                url = _this.$list_may_enroll_csv_btn.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: function() {
                        _this.$reports_request_response_error.text(
                            gettext("Error generating list of students who may enroll. Please try again.")
                        );
                        $(".msg-error").css({
                            "display": "block"
                        });
                    },
                    success: function(data) {
                        _this.$reports_request_response.text(data.status);
                        $(".msg-confirm").css({
                            "display": "block"
                        });
                    }
                });
            });
            this.$grade_config_btn.click(function() {
                var url;
                url = _this.$grade_config_btn.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: function() {
                        _this.clear_display();
                        _this.$download_request_response_error.text(gettext("Error retrieving grading configuration."));
                    },
                    success: function(data) {
                        _this.clear_display();
                        _this.$download_display_text.html(data.grading_config_summary);
                    }
                });
            });
            this.$async_report_btn.click(function(e) {
                var url;
                _this.clear_display();
                url = $(e.target).data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    error: std_ajax_err(function() {
                        if (e.target.name === 'calculate-grades-csv') {
                            _this.$grades_request_response_error.text(
                                gettext("Error generating grades. Please try again."))
                            ;
                        } else if (e.target.name === 'problem-grade-report') {
                            _this.$grades_request_response_error.text(
                                gettext("Error generating problem grade report. Please try again.")
                            );
                        } else if (e.target.name === 'export-ora2-data') {
                            _this.$grades_request_response_error.text(
                                gettext("Error generating ORA data report. Please try again.")
                            );
                        }
                        $(".msg-error").css({
                            "display": "block"
                        });
                    }),
                    success: function(data) {
                        _this.$reports_request_response.text(data.status);
                        $(".msg-confirm").css({
                            "display": "block"
                        });
                    }
                });
            });
        }

        DataDownload.prototype.onClickTitle = function() {
            this.clear_display();
            this.instructor_tasks.task_poller.start();
            this.report_downloads.downloads_poller.start();
        };

        DataDownload.prototype.onExit = function() {
            this.instructor_tasks.task_poller.stop();
            this.report_downloads.downloads_poller.stop();
        };

        DataDownload.prototype.clear_display = function() {
            this.$download_display_text.empty();
            this.$download_display_table.empty();
            this.$download_request_response_error.empty();
            this.$reports_request_response.empty();
            this.$reports_request_response_error.empty();
            $(".msg-confirm").css({
                "display": "none"
            });
            $(".msg-error").css({
                "display": "none"
            });
        };

        return DataDownload;

    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        DataDownload: DataDownload
    });

}).call(this, Slick, DataDownload_Certificate);  // jshint ignore:line
