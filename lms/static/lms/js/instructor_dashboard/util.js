(function() {
    'use strict';

    var IntervalManager, KeywordValidator, ReportDownloads, create_email_content_table, create_email_message_views, find_and_assert, p_wrapper, plantInterval, plantTimeout, sent_to_formatter, setup_copy_email_button, subject_formatter, unknown_if_null_formatter, unknown_p,
        _this = this,
        __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

    plantTimeout = function(ms, cb) {
        return setTimeout(cb, ms);
    };

    plantInterval = function(ms, cb) {
        return setInterval(cb, ms);
    };

    find_and_assert = function($root, selector) {
        var item;
        item = $root.find(selector);
        if (item.length !== 1) {
            console.error("element selection failed for '" + selector + "' resulted in length " + item.length);
            throw "Failed Element Selection";
        } else {
            return item;
        }
    };

    this.std_ajax_err = function(handler) {
        return function(jqXHR, textStatus, errorThrown) {
            console.warn("ajax error\ntextStatus: " + textStatus + "\nerrorThrown: " + errorThrown);
            return handler.apply(this, arguments);
        };
    };

    this.create_task_list_table = function($table_tasks, tasks_data) {
        var $table_placeholder, columns, grid, options, table_data;
        $table_tasks.empty();
        options = {
            enableCellNavigation: true,
            enableColumnReorder: false,
            autoHeight: true,
            rowHeight: 100,
            forceFitColumns: true
        };
        columns = [
            {
                id: 'task_type',
                field: 'task_type',
                /*
                 Translators: a "Task" is a background process such as grading students or sending email
                 */

                name: gettext('Task Type'),
                minWidth: 102
            }, {
                id: 'task_input',
                field: 'task_input',
                /*
                 Translators: a "Task" is a background process such as grading students or sending email
                 */

                name: gettext('Task inputs'),
                minWidth: 150
            }, {
                id: 'task_id',
                field: 'task_id',
                /*
                 Translators: a "Task" is a background process such as grading students or sending email
                 */

                name: gettext('Task ID'),
                minWidth: 150
            }, {
                id: 'requester',
                field: 'requester',
                /*
                 Translators: a "Requester" is a username that requested a task such as sending email
                 */

                name: gettext('Requester'),
                minWidth: 80
            }, {
                id: 'created',
                field: 'created',
                /*
                 Translators: A timestamp of when a task (eg, sending email) was submitted appears after this
                 */

                name: gettext('Submitted'),
                minWidth: 120
            }, {
                id: 'duration_sec',
                field: 'duration_sec',
                /*
                 Translators: The length of a task (eg, sending email) in seconds appears this
                 */

                name: gettext('Duration (sec)'),
                minWidth: 80
            }, {
                id: 'task_state',
                field: 'task_state',
                /*
                 Translators: The state (eg, "In progress") of a task (eg, sending email) appears after this.
                 */

                name: gettext('State'),
                minWidth: 80
            }, {
                id: 'status',
                field: 'status',
                /*
                 Translators: a "Task" is a background process such as grading students or sending email
                 */

                name: gettext('Task Status'),
                minWidth: 80
            }, {
                id: 'task_message',
                field: 'task_message',
                /*
                 Translators: a "Task" is a background process such as grading students or sending email
                 */

                name: gettext('Task Progress'),
                minWidth: 120
            }
        ];
        table_data = tasks_data;
        $table_placeholder = $('<div/>', {
            "class": 'slickgrid'
        });
        $table_tasks.append($table_placeholder);
        grid = new Slick.Grid($table_placeholder, table_data, columns, options);
    };

    subject_formatter = function(row, cell, value, columnDef, dataContext) {
        var subject_text;
        if (value === null) {
            return gettext("An error occurred retrieving your email. Please try again later, and contact technical support if the problem persists.");
        }
        subject_text = $('<span>').text(value['subject']).html();
        return edx.HtmlUtils.joinHtml(
            edx.HtmlUtils.HTML('<p><a href="#email_message_'), 
            value['id'],
            edx.HtmlUtils.HTML('" id="email_message_'),
            value['id'],
            edx.HtmlUtils.HTML('_trig">'),
            subject_text,
            edx.HtmlUtils.HTML('</a></p>')
        );
    };

    p_wrapper = function(value) {
        return edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), value, edx.HtmlUtils.HTML('</p>'));
    };

    unknown_p = function() {
        return p_wrapper(gettext('Unknown'));
    };

    sent_to_formatter = function(row, cell, value, columnDef, dataContext) {
        if (value === null) {
            return unknown_p();
        } else {
            return p_wrapper(value.join(", "));
        }
    };

    unknown_if_null_formatter = function(row, cell, value, columnDef, dataContext) {
        if (value === null) {
            return unknown_p();
        } else {
            return p_wrapper(value);
        }
    };

    create_email_content_table = function($table_emails, $table_emails_inner, email_data) {
        var $table_placeholder, columns, grid, options, table_data;
        $table_emails_inner.empty();
        $table_emails.show();
        options = {
            enableCellNavigation: true,
            enableColumnReorder: false,
            autoHeight: true,
            rowHeight: 50,
            forceFitColumns: true
        };
        columns = [
            {
                id: 'email',
                field: 'email',
                name: gettext('Subject'),
                minWidth: 80,
                cssClass: "email-content-cell",
                formatter: subject_formatter
            }, {
                id: 'requester',
                field: 'requester',
                name: gettext('Sent By'),
                minWidth: 80,
                maxWidth: 100,
                cssClass: "email-content-cell",
                formatter: unknown_if_null_formatter
            }, {
                id: 'sent_to',
                field: 'sent_to',
                name: gettext('Sent To'),
                minWidth: 80,
                maxWidth: 100,
                cssClass: "email-content-cell",
                formatter: sent_to_formatter
            }, {
                id: 'created',
                field: 'created',
                name: gettext('Time Sent'),
                minWidth: 80,
                cssClass: "email-content-cell",
                formatter: unknown_if_null_formatter
            }, {
                id: 'number_sent',
                field: 'number_sent',
                name: gettext('Number Sent'),
                minwidth: 100,
                maxWidth: 150,
                cssClass: "email-content-cell",
                formatter: unknown_if_null_formatter
            }
        ];
        table_data = email_data;
        $table_placeholder = $('<div/>', {
            "class": 'slickgrid'
        });
        $table_emails_inner.append($table_placeholder);
        grid = new Slick.Grid($table_placeholder, table_data, columns, options);
        return $table_emails.append($('<br/>'));
    };

    create_email_message_views = function($messages_wrapper, emails) {
        var $close_button, $created, $email_content, $email_content_header, $email_header, $email_wrapper, $message, $message_content, $requester, $sent_to, $subject, email_id, email_info, interpolate_header, _i, _len;
        $messages_wrapper.empty();
        for (_i = 0, _len = emails.length; _i < _len; _i++) {
            email_info = emails[_i];
            if (!email_info.email) {
                return;
            }
            email_id = email_info.email['id'];
            $message_content = $('<section>', {
                "aria-hidden": "true",
                "class": "modal email-modal",
                id: "email_message_" + email_id
            });
            $email_wrapper = $('<div>', {
                "class": 'inner-wrapper email-content-wrapper'
            });
            $email_header = $('<div>', {
                "class": 'email-content-header'
            });
            $email_header.append($('<input>', {
                type: "button",
                name: "copy-email-body-text",
                value: gettext("Copy Email To Editor"),
                id: "copy_email_" + email_id
            }));
            $close_button = $('<a>', {
                href: '#',
                "class": "close-modal"
            });
            $close_button.append($('<i>', {
                "class": 'icon fa fa-times'
            }));
            $email_header.append($close_button);
            interpolate_header = function(title, value) {
                return edx.HtmlUtils.setHtml($('<h2>', {
                    "class": 'message-bold'
                }), edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<em>'), title, edx.HtmlUtils.HTML('</em>'), value));
            };
            $subject = interpolate_header(gettext('Subject:'), email_info.email['subject']);
            $requester = interpolate_header(gettext('Sent By:'), email_info.requester);
            $created = interpolate_header(gettext('Time Sent:'), email_info.created);
            $sent_to = interpolate_header(gettext('Sent To:'), email_info.sent_to.join(", "));
            $email_header.append($subject);
            $email_header.append($requester);
            $email_header.append($created);
            $email_header.append($sent_to);
            $email_wrapper.append($email_header);
            $email_wrapper.append($('<hr>'));
            $email_content = $('<div>', {
                "class": 'email-content-message'
            });
            $email_content_header = edx.HtmlUtils.setHtml($('<h2>', {
                "class": "message-bold"
            }), edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<em>'), gettext("Message:"), edx.HtmlUtils.HTML('</em>')));
            $email_content.append($email_content_header);
            $message = edx.HtmlUtils.setHtml($('<div>'), edx.HtmlUtils.HTML(email_info.email['html_message']));
            $email_content.append($message);
            $email_wrapper.append($email_content);
            $message_content.append($email_wrapper);
            $messages_wrapper.append($message_content);
            $('#email_message_' + email_info.email['id'] + '_trig').leanModal({
                closeButton: ".close-modal",
                copyEmailButton: "#copy_email_" + email_id
            });
            setup_copy_email_button(email_id, email_info.email['html_message'], email_info.email['subject']);
        }
    };

    setup_copy_email_button = function(email_id, html_message, subject) {
        var _this = this;
        return $("#copy_email_" + email_id).click(function() {
            var editor;
            editor = tinyMCE.get("mce_0");
            editor.setContent(html_message);
            return $('#id_subject').val(subject);
        });
    };

    IntervalManager = (function() {

        function IntervalManager(ms, fn) {
            this.ms = ms;
            this.fn = fn;
            this.intervalID = null;
        }

        IntervalManager.prototype.start = function() {
            this.fn();
            if (this.intervalID === null) {
                return this.intervalID = setInterval(this.fn, this.ms);
            }
        };

        IntervalManager.prototype.stop = function() {
            clearInterval(this.intervalID);
            return this.intervalID = null;
        };

        return IntervalManager;

    })();

    this.PendingInstructorTasks = (function() {
        /* Pending Instructor Tasks Section
         */

        function PendingInstructorTasks($section) {
            var TASK_LIST_POLL_INTERVAL,
                _this = this;
            this.$section = $section;
            this.reload_running_tasks_list = function() {
                return PendingInstructorTasks.prototype.reload_running_tasks_list.apply(_this, arguments);
            };
            this.$running_tasks_section = find_and_assert(this.$section, ".running-tasks-section");
            this.$table_running_tasks = find_and_assert(this.$section, ".running-tasks-table");
            this.$no_tasks_message = find_and_assert(this.$section, ".no-pending-tasks-message");
            if (this.$table_running_tasks.length) {
                TASK_LIST_POLL_INTERVAL = 20000;
                this.reload_running_tasks_list();
                this.task_poller = new IntervalManager(TASK_LIST_POLL_INTERVAL, function() {
                    return _this.reload_running_tasks_list();
                });
            }
        }

        PendingInstructorTasks.prototype.reload_running_tasks_list = function() {
            var list_endpoint,
                _this = this;
            list_endpoint = this.$table_running_tasks.data('endpoint');
            return $.ajax({
                type: 'POST',
                dataType: 'json',
                url: list_endpoint,
                success: function(data) {
                    if (data.tasks.length) {
                        create_task_list_table(_this.$table_running_tasks, data.tasks);
                        _this.$no_tasks_message.hide();
                        return _this.$running_tasks_section.show();
                    } else {
                        console.log("No pending tasks to display");
                        _this.$running_tasks_section.hide();
                        _this.$no_tasks_message.empty();
                        _this.$no_tasks_message.append($('<p>').text(gettext("No tasks currently running.")));
                        return _this.$no_tasks_message.show();
                    }
                },
                error: std_ajax_err(function() {
                    return console.error("Error finding pending tasks to display");
                })
            });
            /* /Pending Instructor Tasks Section
             */

        };

        return PendingInstructorTasks;

    })();

    KeywordValidator = (function() {

        function KeywordValidator() {}

        KeywordValidator.keyword_regex = /%%+[^%]+%%/g;

        KeywordValidator.keywords = ['%%USER_ID%%', '%%USER_FULLNAME%%', '%%COURSE_DISPLAY_NAME%%', '%%COURSE_END_DATE%%'];

        KeywordValidator.validate_string = function(string) {
            var found_keyword, found_keywords, invalid_keywords, is_valid, keywords, regex_match, _fn, _i, _len;
            regex_match = string.match(KeywordValidator.keyword_regex);
            found_keywords = regex_match === null ? [] : regex_match;
            invalid_keywords = [];
            is_valid = true;
            keywords = KeywordValidator.keywords;
            _fn = function(found_keyword) {
                if (__indexOf.call(keywords, found_keyword) < 0) {
                    return invalid_keywords.push(found_keyword);
                }
            };
            for (_i = 0, _len = found_keywords.length; _i < _len; _i++) {
                found_keyword = found_keywords[_i];
                _fn(found_keyword);
            }
            if (invalid_keywords.length !== 0) {
                is_valid = false;
            }
            return {
                is_valid: is_valid,
                invalid_keywords: invalid_keywords
            };
        };

        return KeywordValidator;

    }).call(this);

    ReportDownloads = (function() {
        /* Report Downloads -- links expire quickly, so we refresh every 5 mins
         */

        function ReportDownloads($section) {
            var POLL_INTERVAL,
                _this = this;
            this.$section = $section;
            this.$report_downloads_table = this.$section.find(".report-downloads-table");
            POLL_INTERVAL = 20000;
            this.downloads_poller = new window.InstructorDashboard.util.IntervalManager(POLL_INTERVAL, function() {
                return _this.reload_report_downloads();
            });
        }

        ReportDownloads.prototype.reload_report_downloads = function() {
            var endpoint,
                _this = this;
            endpoint = this.$report_downloads_table.data('endpoint');
            return $.ajax({
                type: 'POST',
                dataType: 'json',
                url: endpoint,
                success: function(data) {
                    if (data.downloads.length) {
                        return _this.create_report_downloads_table(data.downloads);
                    } else {
                        return console.log("No reports ready for download");
                    }
                },
                error: function(std_ajax_err) {
                    return console.error("Error finding report downloads");
                }
            });
        };

        ReportDownloads.prototype.create_report_downloads_table = function(report_downloads_data) {
            var $table_placeholder, columns, grid, options,
                _this = this;
            this.$report_downloads_table.empty();
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
                    minWidth: 150,
                    cssClass: "file-download-link",
                    formatter: function(row, cell, value, columnDef, dataContext) {
                        return edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<a target="_blank" href="'), dataContext['url'], edx.HtmlUtils.HTML('">'), dataContext['name'], edx.HtmlUtils.HTML('</a>'));
                    }
                }
            ];
            $table_placeholder = $('<div/>', {
                "class": 'slickgrid'
            });
            this.$report_downloads_table.append($table_placeholder);
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
        };

        return ReportDownloads;

    })();

    if (typeof _ !== "undefined" && _ !== null) {
        _.defaults(window, {
            InstructorDashboard: {}
        });
        window.InstructorDashboard.util = {
            plantTimeout: plantTimeout,
            plantInterval: plantInterval,
            std_ajax_err: window.std_ajax_err,
            IntervalManager: IntervalManager,
            create_task_list_table: window.create_task_list_table,
            create_email_content_table: create_email_content_table,
            create_email_message_views: create_email_message_views,
            PendingInstructorTasks: window.PendingInstructorTasks,
            KeywordValidator: KeywordValidator,
            ReportDownloads: ReportDownloads
        };
    }

}).call(this);
