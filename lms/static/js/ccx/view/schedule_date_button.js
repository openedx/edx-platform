/* eslint no-shadow: "off" */
(function(define) {
    'use strict';
    define([
        'backbone',
        'jquery',
        'underscore',
        'gettext',
        'text!templates/ccx/underscore/date-button.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(Backbone,
        $,
        _,
        gettext,
        scheduleTreeDateButtonTemplate,
        HtmlUtils) {
        return Backbone.View.extend({

            initialize: function(options) {
                this.dateType = options.dateType;
                this.date = options.date;
                this.template = HtmlUtils.template(scheduleTreeDateButtonTemplate);
            },

            render: function() {
                var $dateChangeButton;
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({date: this.date})
                );
                this.location = this.$el.data('location');
                $dateChangeButton = $(this.$el.find('button'));

                $dateChangeButton.attr('href', '#enter-date-modal').leanModal({closeButton: '.close-modal'});
                $dateChangeButton.click(this.editDateCCXSchedule());

                return this;
            },

            editDateCCXSchedule: function() {
                var self = this;
                return function() {
                    var dateParts;
                    var date;
                    var time;
                    var row = $(this).closest('tr');
                    var modal = $('#enter-date-modal')
                        .data('what', self.dateType)
                        .data('location', row.data('location'));

                    modal.find('h2').text(
                        self.dateType === 'due' ? HtmlUtils.ensureHtml(gettext('Enter Due Date and Time')) :
                            HtmlUtils.ensureHtml(gettext('Enter Start Date and Time'))
                    );

                    if (self.date) {
                        // if already date is set then populate modal with that date.
                        dateParts = self.date ? self.date.split(' ') : ['', ''];
                        date = dateParts[0];
                        time = dateParts[1];

                        modal.find('input[name=date]').val(date);
                        modal.find('input[name=time]').val(time);
                    }

                    modal.focus();
                    $(document).on('focusin', function(event) {
                        try {
                            // When focusin event triggers in document it will detects that if object
                            // is modal (dialog) then it will shift the focus to cross icon
                            // the first element in dialog.
                            if (!_.isUndefined(event.target.closest('.modal').id) &&
                                event.target.closest('.modal').id !== 'enter-date-modal' &&
                                event.target.id !== 'enter-date-modal') {
                                event.preventDefault();
                                modal.find('.close-modal').focus();
                            }
                        } catch (err) {
                            // if error then try to focus close icon.
                            event.preventDefault();
                            modal.find('.close-modal').focus();
                        }
                    });

                    modal.find('.close-modal').click(function() {
                        // on close model click, focus back last selected element.
                        $(document).off('focusin');
                        $(window).scrollTop(self.$el.position().top);
                        self.$el.focus();
                    });

                    modal.find('form').off('submit').on('submit', function(event) {
                        // Submits valid start or due date to ccx_schedule.js file. which process it
                        // and if date is change on subsection then it will propagate change to
                        // child nodes.
                        var newDate;
                        var validTime = /^\d{1,2}:\d{2}?$/;
                        var date = $(this).find('input[name=date]').val(),
                            time = $(this).find('input[name=time]').val();
                        var validDate = new Date(date);

                        event.preventDefault();
                        modal.find('#date-modal-error-message').empty();

                        if (isNaN(validDate.valueOf())) {
                            modal.find('#date-modal-error-message').text(HtmlUtils.ensureHtml(
                                gettext('Please enter a valid date'))
                            );
                            return;
                        }

                        if (!time.match(validTime)) {
                            modal.find('#date-modal-error-message').text(HtmlUtils.ensureHtml(
                                gettext('Please enter a valid time'))
                            );
                            return;
                        }

                        $(window).scrollTop(self.$el.position().top);
                        self.$el.focus();
                        newDate = date + ' ' + time;
                        if (!self.date || newDate !== self.date) {
                            self.trigger(
                                'updateDate', self.dateType, newDate, self.location
                            );
                        }
                        modal.find('.close-modal').click();
                    });
                };
            }
        });
    });
}).call(this, define || RequireJS.define);
