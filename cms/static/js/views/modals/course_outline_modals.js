/**
 * The CourseOutlineXBlockModal is a Backbone view that shows an editor in a modal window.
 * It has nested views: for release date, due date and grading format.
 * It is invoked using the editXBlock method and uses xblock_info as a model,
 * and upon save parent invokes refresh function that fetches updated model and
 * re-renders edited course outline.
 */
define(['jquery', 'backbone', 'underscore', 'gettext', 'js/views/baseview',
    'js/views/modals/base_modal', 'date', 'js/views/utils/xblock_utils',
    'js/utils/date_utils'
], function(
    $, Backbone, _, gettext, BaseView, BaseModal, date, XBlockViewUtils, DateUtils
) {
    'use strict';
    var CourseOutlineXBlockModal, SettingsXBlockModal, PublishXBlockModal, AbstractEditor, BaseDateEditor,
        ReleaseDateEditor, DueDateEditor, GradingEditor, PublishEditor, StaffLockEditor,
        VerificationAccessEditor, TimedExaminationPreferenceEditor;

    CourseOutlineXBlockModal = BaseModal.extend({
        events : {
            'click .action-save': 'save'
        },

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'course-outline',
            modalType: 'edit-settings',
            addSaveButton: true,
            modalSize: 'med',
            viewSpecificClasses: 'confirm',
            editors: []
        }),

        initialize: function() {
            BaseModal.prototype.initialize.call(this);
            this.events = $.extend({}, BaseModal.prototype.events, this.events);
            this.template = this.loadTemplate('course-outline-modal');
            this.options.title = this.getTitle();
        },

        afterRender: function () {
            BaseModal.prototype.afterRender.call(this);
            this.initializeEditors();
        },

        initializeEditors: function () {
            this.options.editors = _.map(this.options.editors, function (Editor) {
                return new Editor({
                    parentElement: this.$('.modal-section'),
                    model: this.model,
                    xblockType: this.options.xblockType,
                    enable_proctored_exams: this.options.enable_proctored_exams,
                    enable_timed_exams: this.options.enable_timed_exams
                });
            }, this);
        },

        getTitle: function () {
            return '';
        },

        getIntroductionMessage: function () {
            return '';
        },

        getContentHtml: function() {
            return this.template(this.getContext());
        },

        save: function(event) {
            event.preventDefault();
            var requestData = this.getRequestData();
            if (!_.isEqual(requestData, { metadata: {} })) {
                XBlockViewUtils.updateXBlockFields(this.model, requestData, {
                    success: this.options.onSave
                });
            }
            this.hide();
        },

        /**
         * Return context for the modal.
         * @return {Object}
         */
        getContext: function () {
            return $.extend({
                xblockInfo: this.model,
                introductionMessage: this.getIntroductionMessage()
            });
        },

        /**
         * Return request data.
         * @return {Object}
         */
        getRequestData: function () {
            var requestData = _.map(this.options.editors, function (editor) {
                return editor.getRequestData();
            });

            return $.extend.apply(this, [true, {}].concat(requestData));
        }
    });

    SettingsXBlockModal = CourseOutlineXBlockModal.extend({
        getTitle: function () {
            return interpolate(
                gettext('%(display_name)s Settings'),
                { display_name: this.model.get('display_name') }, true
            );
        },

        getIntroductionMessage: function () {
            return interpolate(
                gettext('Change the settings for %(display_name)s'),
                { display_name: this.model.get('display_name') }, true
            );
        }
    });


    PublishXBlockModal = CourseOutlineXBlockModal.extend({
        events : {
            'click .action-publish': 'save'
        },

        initialize: function() {
            CourseOutlineXBlockModal.prototype.initialize.call(this);
            if (this.options.xblockType) {
                this.options.modalName = 'bulkpublish-' + this.options.xblockType;
            }
        },

        getTitle: function () {
            return interpolate(
                gettext('Publish %(display_name)s'),
                { display_name: this.model.get('display_name') }, true
            );
        },

        getIntroductionMessage: function () {
            return interpolate(
                gettext('Publish all unpublished changes for this %(item)s?'),
                { item: this.options.xblockType }, true
            );
        },

        addActionButtons: function() {
            this.addActionButton('publish', gettext('Publish'), true);
            this.addActionButton('cancel', gettext('Cancel'));
        }
    });


    AbstractEditor = BaseView.extend({
        tagName: 'section',
        templateName: null,
        initialize: function() {
            this.template = this.loadTemplate(this.templateName);
            this.parentElement = this.options.parentElement;
            this.render();
        },

        render: function () {
            var html = this.template($.extend({}, {
                xblockInfo: this.model,
                xblockType: this.options.xblockType,
                enable_proctored_exam: this.options.enable_proctored_exams,
                enable_timed_exam: this.options.enable_timed_exams
            }, this.getContext()));

            this.$el.html(html);
            this.parentElement.append(this.$el);
        },

        getContext: function () {
            return {};
        },

        getRequestData: function () {
            return {};
        }
    });

    BaseDateEditor = AbstractEditor.extend({
        // Attribute name in the model, should be defined in children classes.
        fieldName: null,

        events : {
            'click .clear-date': 'clearValue'
        },

        afterRender: function () {
            AbstractEditor.prototype.afterRender.call(this);
            this.$('input.date').datepicker({'dateFormat': 'm/d/yy'});
            this.$('input.time').timepicker({
                'timeFormat' : 'H:i',
                'forceRoundTime': false
            });
            if (this.model.get(this.fieldName)) {
                DateUtils.setDate(
                    this.$('input.date'), this.$('input.time'),
                    this.model.get(this.fieldName)
                );
            }
        }
    });

    DueDateEditor = BaseDateEditor.extend({
        fieldName: 'due',
        templateName: 'due-date-editor',
        className: 'modal-section-content has-actions due-date-input grading-due-date',

        getValue: function () {
            return DateUtils.getDate(this.$('#due_date'), this.$('#due_time'));
        },

        clearValue: function (event) {
            event.preventDefault();
            this.$('#due_time, #due_date').val('');
        },

        getRequestData: function () {
            return {
                metadata: {
                    'due': this.getValue()
                }
            };
        }
    });

    ReleaseDateEditor = BaseDateEditor.extend({
        fieldName: 'start',
        templateName: 'release-date-editor',
        className: 'edit-settings-release scheduled-date-input',
        startingReleaseDate: null,

        afterRender: function () {
            BaseDateEditor.prototype.afterRender.call(this);
            // Store the starting date and time so that we can determine if the user
            // actually changed it when "Save" is pressed.
            this.startingReleaseDate = this.getValue();
        },

        getValue: function () {
            return DateUtils.getDate(this.$('#start_date'), this.$('#start_time'));
        },

        clearValue: function (event) {
            event.preventDefault();
            this.$('#start_time, #start_date').val('');
        },

        getRequestData: function () {
            var newReleaseDate = this.getValue();
            if (JSON.stringify(newReleaseDate) === JSON.stringify(this.startingReleaseDate)) {
                return {};
            }
            return {
                metadata: {
                    'start': newReleaseDate
                }
            };
        }
    });
    TimedExaminationPreferenceEditor = AbstractEditor.extend({
        templateName: 'timed-examination-preference-editor',
        className: 'edit-settings-timed-examination',
        events : {
            'change #id_not_timed': 'notTimedExam',
            'change #id_timed_exam': 'showTimeLimit',
            'change #id_practice_exam': 'showTimeLimit',
            'change #id_proctored_exam': 'showTimeLimit',
            'focusout #id_time_limit': 'timeLimitFocusout'
        },
        notTimedExam: function (event) {
            event.preventDefault();
            this.$('#id_time_limit_div').hide();
            this.$('#id_time_limit').val('00:00');
        },
        showTimeLimit: function (event) {
            event.preventDefault();
            this.$('#id_time_limit_div').show();
            this.$('#id_time_limit').val("00:30");
        },
        timeLimitFocusout: function(event) {
            event.preventDefault();
            var selectedTimeLimit = $(event.currentTarget).val();
            if (!this.isValidTimeLimit(selectedTimeLimit)) {
                $(event.currentTarget).val("00:30");
            }
        },
        afterRender: function () {
            AbstractEditor.prototype.afterRender.call(this);
            this.$('input.time').timepicker({
                'timeFormat' : 'H:i',
                'minTime': '00:30',
                'maxTime': '05:00',
                'forceRoundTime': false
            });

            this.setExamType(this.model.get('is_time_limited'), this.model.get('is_proctored_exam'),
                            this.model.get('is_practice_exam'));
            this.setExamTime(this.model.get('default_time_limit_minutes'));
        },
        setExamType: function(is_time_limited, is_proctored_exam, is_practice_exam) {
            if (!is_time_limited) {
                this.$("#id_not_timed").prop('checked', true);
                return;
            }

            this.$('#id_time_limit_div').show();

            if (this.options.enable_proctored_exams && is_proctored_exam) {
                if (is_practice_exam) {
                    this.$('#id_practice_exam').prop('checked', true);
                } else {
                    this.$('#id_proctored_exam').prop('checked', true);
                }
            } else {
                // Since we have an early exit at the top of the method
                // if the subsection is not time limited, then
                // here we rightfully assume that it just a timed exam
                this.$("#id_timed_exam").prop('checked', true);
            }
        },
        setExamTime: function(value) {
            var time = this.convertTimeLimitMinutesToString(value);
            this.$('#id_time_limit').val(time);
        },
        isValidTimeLimit: function(time_limit) {
            var pattern = new RegExp('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$');
            return pattern.test(time_limit) && time_limit !== "00:00";
        },
        getExamTimeLimit: function () {
            return this.$('#id_time_limit').val();
        },
        convertTimeLimitMinutesToString: function (timeLimitMinutes) {
            var hoursStr = "" + Math.floor(timeLimitMinutes / 60);
            var actualMinutesStr = "" + (timeLimitMinutes % 60);
            hoursStr = "00".substring(0, 2 - hoursStr.length) + hoursStr;
            actualMinutesStr = "00".substring(0, 2 - actualMinutesStr.length) + actualMinutesStr;
            return hoursStr + ":" + actualMinutesStr;
        },
        convertTimeLimitToMinutes: function (time_limit) {
            var time = time_limit.split(':');
            var total_time = (parseInt(time[0]) * 60) + parseInt(time[1]);
            return total_time;
        },
        getRequestData: function () {
            var is_time_limited;
            var is_practice_exam;
            var is_proctored_exam;
            var time_limit = this.getExamTimeLimit();

            if (this.$("#id_not_timed").is(':checked')){
                is_time_limited = false;
                is_practice_exam = false;
                is_proctored_exam = false;
            } else if (this.$("#id_timed_exam").is(':checked')){
                is_time_limited = true;
                is_practice_exam = false;
                is_proctored_exam = false;
            } else if (this.$("#id_proctored_exam").is(':checked')){
                is_time_limited = true;
                is_practice_exam = false;
                is_proctored_exam = true;
            } else if (this.$("#id_practice_exam").is(':checked')){
                is_time_limited = true;
                is_practice_exam = true;
                is_proctored_exam = true;
            }

            return {
                metadata: {
                    'is_practice_exam': is_practice_exam,
                    'is_time_limited': is_time_limited,
                    // We have to use the legacy field name
                    // as the Ajax handler directly populates
                    // the xBlocks fields. We will have to
                    // update this call site when we migrate
                    // seq_module.py to use 'is_proctored_exam'
                    'is_proctored_enabled': is_proctored_exam,
                    'default_time_limit_minutes': this.convertTimeLimitToMinutes(time_limit)
                }
            };
        }
    });
    GradingEditor = AbstractEditor.extend({
        templateName: 'grading-editor',
        className: 'edit-settings-grading',

        afterRender: function () {
            AbstractEditor.prototype.afterRender.call(this);
            this.setValue(this.model.get('format'));
        },

        setValue: function (value) {
            this.$('#grading_type').val(value);
        },

        getValue: function () {
            return this.$('#grading_type').val();
        },

        getRequestData: function () {
            return {
                'graderType': this.getValue()
            };
        },

        getContext: function () {
            return {
                graderTypes: this.model.get('course_graders')
            };
        }
    });

    PublishEditor = AbstractEditor.extend({
        templateName: 'publish-editor',
        className: 'edit-settings-publish',
        getRequestData: function () {
            return {
                publish: 'make_public'
            };
        }
    });

    StaffLockEditor = AbstractEditor.extend({
        templateName: 'staff-lock-editor',
        className: 'edit-staff-lock',
        isModelLocked: function() {
            return this.model.get('has_explicit_staff_lock');
        },

        isAncestorLocked: function() {
            return this.model.get('ancestor_has_staff_lock');
        },

        afterRender: function () {
            AbstractEditor.prototype.afterRender.call(this);
            this.setLock(this.isModelLocked());
        },

        setLock: function(value) {
            this.$('#staff_lock').prop('checked', value);
        },

        isLocked: function() {
            return this.$('#staff_lock').is(':checked');
        },

        hasChanges: function() {
            return this.isModelLocked() !== this.isLocked();
        },

        getRequestData: function() {
            return this.hasChanges() ? {
                publish: 'republish',
                metadata: {
                    visible_to_staff_only: this.isLocked() ? true : null
                    }
                } : {};
        },

        getContext: function () {
            return {
                hasExplicitStaffLock: this.isModelLocked(),
                ancestorLocked: this.isAncestorLocked()
            };
        }
    });

    VerificationAccessEditor = AbstractEditor.extend({
        templateName: 'verification-access-editor',
        className: 'edit-verification-access',

        // This constant MUST match the group ID
        // defined by VerificationPartitionScheme on the backend!
        ALLOW_GROUP_ID: 1,

        getSelectedPartition: function() {
            var hasRestrictions = $("#verification-access-checkbox").is(":checked"),
                selectedPartitionID = null;

            if (hasRestrictions) {
                selectedPartitionID = $("#verification-partition-select").val();
            }

            return parseInt(selectedPartitionID, 10);
        },

        getGroupAccess: function() {
            var groupAccess = _.clone(this.model.get('group_access')) || [],
                userPartitions = this.model.get('user_partitions') || [],
                selectedPartition = this.getSelectedPartition(),
                that = this;

            // We display a simplified UI to course authors.
            // On the backend, each verification checkpoint is associated
            // with a user partition that has two groups.  For example,
            // if two checkpoints were defined, they might look like:
            //
            // Midterm A: |-- ALLOW --|-- DENY --|
            // Midterm B: |-- ALLOW --|-- DENY --|
            //
            // To make life easier for course authors, we display
            // *one* option for each checkpoint:
            //
            // [X] Must complete verification checkpoint
            //     Dropdown:
            //        * Midterm A
            //        * Midterm B
            //
            // This is where we map the simplified UI to
            // the underlying user partition.  If the user checked
            // the box, that means there *is* a restriction,
            // so only the "ALLOW" group for the selected partition has access.
            // Otherwise, all groups in the partition have access.
            //
            _.each(userPartitions, function(partition) {
                if (partition.scheme === "verification") {
                    if (selectedPartition === partition.id) {
                        groupAccess[partition.id] = [that.ALLOW_GROUP_ID];
                    } else {
                        delete groupAccess[partition.id];
                    }
                }
            });

            return groupAccess;
        },

        getRequestData: function() {
            var groupAccess = this.getGroupAccess(),
                hasChanges = !_.isEqual(groupAccess, this.model.get('group_access'));

            return hasChanges ? {
                publish: 'republish',
                metadata: {
                    group_access: groupAccess,
                }
            } : {};
        },

        getContext: function() {
            var partitions = this.model.get("user_partitions"),
                hasRestrictions = false,
                verificationPartitions = [],
                isSelected = false;

            // Display a simplified version of verified partition schemes.
            // Although there are two groups defined (ALLOW and DENY),
            // we show only the ALLOW group.
            // To avoid searching all the groups, we're assuming that the editor
            // either sets the ALLOW group or doesn't set any groups (implicitly allow all).
            _.each(partitions, function(item) {
                if (item.scheme === "verification") {
                    isSelected = _.any(_.pluck(item.groups, "selected"));
                    hasRestrictions = hasRestrictions || isSelected;

                    verificationPartitions.push({
                        "id": item.id,
                        "name": item.name,
                        "selected": isSelected,
                    });
                }
            });

            return {
                "hasVerificationRestrictions": hasRestrictions,
                "verificationPartitions": verificationPartitions,
            };
        }
    });

    return {
        getModal: function (type, xblockInfo, options) {
            if (type === 'edit') {
                return this.getEditModal(xblockInfo, options);
            } else if (type === 'publish') {
                return this.getPublishModal(xblockInfo, options);
            }
        },

        getEditModal: function (xblockInfo, options) {
            var editors = [];

            if (xblockInfo.isChapter()) {
                editors = [ReleaseDateEditor, StaffLockEditor];
            } else if (xblockInfo.isSequential()) {
                editors = [ReleaseDateEditor, GradingEditor, DueDateEditor];

                var enable_special_exams = (options.enable_proctored_exams || options.enable_timed_exams);
                if (enable_special_exams) {
                    editors.push(TimedExaminationPreferenceEditor);
                }

                editors.push(StaffLockEditor);

            } else if (xblockInfo.isVertical()) {
                editors = [StaffLockEditor];

                if (xblockInfo.hasVerifiedCheckpoints()) {
                    editors.push(VerificationAccessEditor);
                }
            }
            /* globals course */
            if (course.get('self_paced')) {
                editors = _.without(editors, ReleaseDateEditor, DueDateEditor);
            }
            return new SettingsXBlockModal($.extend({
                editors: editors,
                model: xblockInfo
            }, options));
        },

        getPublishModal: function (xblockInfo, options) {
            return new PublishXBlockModal($.extend({
                editors: [PublishEditor],
                model: xblockInfo
            }, options));
        }
    };
});
