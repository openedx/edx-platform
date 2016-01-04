;(function (define) {
    'use strict';
    define([
            'backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!templates/ccx/underscore/right-container.underscore',
            'text!templates/ccx/underscore/form.underscore',
            'edx-ui-toolkit/js/utils/html-utils',
            'jquery.timepicker'
        ],
        function (Backbone,
                  $,
                  _,
                  gettext,
                  scheduleRightContainerTemplate,
                  scheduleFormTemplate,
                  HtmlUtils) {
            return Backbone.View.extend({

                events: {
                    'change select#ccx_chapter': 'onChapterSelect',
                    'change select#ccx_sequential': 'onSubsectionSelect',
                    'change select#ccx_vertical': 'onVerticalSelect',
                    'change .date': 'onDateSelect',
                    'click #add-unit-button': 'addUnitInScheduleTree',
                    'click #add-all': 'showAllUnitsInScheduleTree',
                    'click #save-changes': 'saveSchedule'
                },

                initialize: function (options) {
                    this.templateContainer = HtmlUtils.template(scheduleRightContainerTemplate);
                    this.templateForm = HtmlUtils.template(scheduleFormTemplate);
                    this.unsavedChanges = options.unsavedChanges;

                    // Hidden data will be shown into form,
                    // from there user can add this data to schedule tree
                    this.chapters = this.collection.filterFormData();
                    this.resetFormFlags();
                },

                render: function () {
                    if (this.chapters) {
                        this.loadRightContainerCCXSchedule();
                    }

                    return this;
                },

                loadRightContainerCCXSchedule: function () {
                    HtmlUtils.setHtml(
                        this.$el,
                        this.templateContainer({
                            chaptersAvailable: (this.chapters && !_.isEmpty(this.chapters)),
                            unsavedChanges: this.unsavedChanges,
                            addUnitCCXForm: this.templateForm({
                                chapters: this.chapters,
                                selectedChapter: this.selectedChapter,
                                selectedSubsection: this.selectedSubsection,
                                enableAddUnitToScheduleButton: this.enableAddUnitToScheduleButton
                            })
                        })
                    );

                    // attach date and time pickers
                    this.$el.find('.datepair .time').timepicker({
                        'showDuration': true,
                        'timeFormat': 'G:i',
                        'autoclose': true
                    });

                    this.$el.find('.datepair .date').datepicker({
                        'dateFormat': 'yy-mm-dd',
                        'autoclose': true
                    });
                },


                addUnitInScheduleTree: function (e) {
                    // add unit to schedule tree. To make contents visible to students
                    // a unit can be chapter, sequential or a vertical.
                    e.preventDefault();
                    var chapterLocation = this.$el.find("#ccx_chapter").val();
                    var sequentialLocation = this.$el.find("#ccx_sequential").val();
                    var verticalLocation = this.$el.find("#ccx_vertical").val();
                    var startDate = this.getDateTime("start");
                    var dueDate = this.getDateTime("due");

                    this.trigger(
                        'showUnitInScheduleTree',
                        chapterLocation,
                        sequentialLocation === 'all' ? null : sequentialLocation,
                        verticalLocation === 'all' ? null : verticalLocation,
                        startDate,
                        dueDate
                    );
                },

                showAllUnitsInScheduleTree: function (e) {
                    // add unit to schedule tree.
                    e.preventDefault();
                    this.trigger(
                        'showAllUnitsInScheduleTree'
                    );
                },

                onChapterSelect: function (e) {
                    // On chapter select populate subsection drop box.
                    var $chapterSelect = $(e.currentTarget);
                    var chapterLocation = $chapterSelect.val();
                    var $sequentialSelect = this.$el.find('#ccx_sequential');
                    if (chapterLocation !== 'none') {
                        this.selectedChapter = this.collection.findUnit(
                            this.chapters, chapterLocation
                        );
                        this.enableAddUnitToScheduleButton = true;
                        $sequentialSelect.empty();
                        this.render();
                    } else {
                        this.resetFormFlags();
                        this.render();
                    }
                },

                onSubsectionSelect: function (e) {
                    // On subsection aka sequential select populate verticals drop box.
                    var $subSectionSelect = $(e.currentTarget);
                    var subSectionLocation = $subSectionSelect.val();
                    var $verticalSelect = this.$el.find('#ccx_vertical');

                    if (subSectionLocation !== 'all') {
                        this.selectedSubsection = this.collection.findUnit(
                            this.chapters,
                            this.selectedChapter.location,
                            subSectionLocation
                        );
                        $verticalSelect.empty();
                        this.render();
                    } else {
                        this.resetSubsectionSelectFlags();
                        this.render();
                    }
                },

                onVerticalSelect: function (e) {
                    // On vertical select disable edit date sections.
                    var $verticalSelect = $(e.currentTarget);
                    var verticalLocation = $verticalSelect.val();

                    if (verticalLocation !== 'all') {
                        this.disableFields(this.$('.ccx_start_date_time_fields'));
                        this.disableFields(this.$('.ccx_due_date_time_fields'));
                    } else {
                        this.enableFields(this.$('.ccx_start_date_time_fields'));
                        this.enableFields(this.$('.ccx_due_date_time_fields'));
                    }
                },

                saveSchedule: function (e) {
                    // save schedule on server.
                    e.preventDefault();
                    var $button = $(e.currentTarget);
                    $button.prop('disabled', true).text(gettext("Saving"));
                    this.trigger(
                        'saveSchedule'
                    );
                },

                resetSaveChangesButton: function () {
                    // After collection save enable save changes button
                    this.$el.find('#save-changes').prop(
                        'disabled', false
                    ).text(gettext("Save changes"));
                },

                onDateSelect: function (e) {
                    // on date select from date picker format it.
                    var $date = $(e.currentTarget);
                    var date = $date.datepicker("getDate");

                    if (date) {
                        HtmlUtils.setHtml(
                            $(this),
                            $.datepicker.formatDate("yy-mm-dd", date)
                        );
                    }
                },

                resetFormFlags: function () {
                    // reset for flag to disable select boxes (subsection, units)
                    // and edit date sections.
                    this.selectedChapter = undefined;
                    this.resetSubsectionSelectFlags();
                    this.enableAddUnitToScheduleButton = false;
                },

                resetSubsectionSelectFlags: function () {
                    // reset for flag to disable select box (units)
                    // and edit date sections.
                    this.selectedSubsection = undefined;
                },

                disableFields: function ($selector) {
                    // disable select, input or button field under selector.
                    $selector.find('select,input,button').prop('disabled', true);
                },

                enableFields: function ($selector) {
                    // enable select, input or button field under selector.
                    $selector.find('select,input,button').prop('disabled', false);
                },

                getDateTime: function (dateType) {
                    var date = this.$('input[name=' + dateType + '_date]').val();
                    var time = this.$('input[name=' + dateType + '_time]').val();
                    time = _.isEmpty(time) ? "00:00" : time;
                    if (date && time) {
                        return date + ' ' + time;
                    }
                    return null;
                }
            });
        }
    );
}).call(this, define || RequireJS.define);