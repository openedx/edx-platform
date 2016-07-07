/**
 * E-Commerce Section
 */
(function() {
    'use strict';

    var ECommerce, PendingInstructorTasks, ReportDownloads;

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    ReportDownloads = function() {
        return window.InstructorDashboard.util.ReportDownloads;
    };

    ECommerce = (function() {
        var isInt;

        function ECommerce($section) {
            var _this = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            this.$list_sale_csv_btn = this.$section.find('input[name="list-sale-csv"]');
            this.$list_order_sale_csv_btn = this.$section.find('input[name="list-order-sale-csv"]');
            this.$download_company_name = this.$section.find('input[name="download_company_name"]');
            this.$active_company_name = this.$section.find('input[name="active_company_name"]');
            this.$spent_company_name = this.$section.find('input[name="spent_company_name"]');
            this.$download_coupon_codes = this.$section.find('input[name="download-coupon-codes-csv"]');
            this.$download_registration_codes_form = this.$section.find('form#download_registration_codes');
            this.$active_registration_codes_form = this.$section.find('form#active_registration_codes');
            this.$spent_registration_codes_form = this.$section.find('form#spent_registration_codes');
            this.$reports = this.$section.find('.reports-download-container');
            this.$reports_request_response = this.$reports.find('.request-response');
            this.$reports_request_response_error = this.$reports.find('.request-response-error');
            this.report_downloads = new (ReportDownloads())(this.$section);
            this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            this.$error_msg = this.$section.find('#error-msg');
            this.$list_sale_csv_btn.click(function() {
                var url;
                url = _this.$list_sale_csv_btn.data('endpoint');
                url += '/csv';
                location.href = url;
            });
            this.$list_order_sale_csv_btn.click(function() {
                var url;
                url = _this.$list_order_sale_csv_btn.data('endpoint');
                location.href = url;
            });
            this.$download_coupon_codes.click(function() {
                var url;
                url = _this.$download_coupon_codes.data('endpoint');
                location.href = url;
            });
            this.$download_registration_codes_form.submit(function() {
                _this.$error_msg.attr('style', 'display: none');
                return true;
            });
            this.$active_registration_codes_form.submit(function() {
                _this.$error_msg.attr('style', 'display: none');
                return true;
            });
            this.$spent_registration_codes_form.submit(function() {
                _this.$error_msg.attr('style', 'display: none');
                return true;
            });
        }

        ECommerce.prototype.onClickTitle = function() {
            this.clear_display();
            this.instructor_tasks.task_poller.start();
            return this.report_downloads.downloads_poller.start();
        };

        ECommerce.prototype.onExit = function() {
            this.clear_display();
            this.instructor_tasks.task_poller.stop();
            return this.report_downloads.downloads_poller.stop();
        };

        ECommerce.prototype.clear_display = function() {
            this.$error_msg.attr('style', 'display: none');
            this.$download_company_name.val('');
            this.$reports_request_response.empty();
            this.$reports_request_response_error.empty();
            this.$active_company_name.val('');
            return this.$spent_company_name.val('');
        };

        isInt = function(n) {
            return n % 1 === 0;
        };

        return ECommerce;

    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        ECommerce: ECommerce
    });

}).call(this);
