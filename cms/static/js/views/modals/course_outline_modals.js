/**
 * The CourseOutlineXBlockModal is a Backbone view that shows an editor in a modal window.
 * It has nested views: for release date, due date and grading format.
 * It is invoked using the editXBlock method and uses xblock_info as a model,
 * and upon save parent invokes refresh function that fetches updated model and
 * re-renders edited course outline.
 */
define(['jquery', 'backbone', 'underscore', 'gettext', 'js/views/baseview',
    'js/views/modals/base_modal', 'date', 'js/views/utils/xblock_utils',
    'js/utils/date_utils', 'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils'
], function(
    $, Backbone, _, gettext, BaseView, BaseModal, date, XBlockViewUtils, DateUtils, HtmlUtils, StringUtils
) {
    'use strict';
    var CourseOutlineXBlockModal, SettingsXBlockModal, PublishXBlockModal, AbstractEditor, BaseDateEditor,
        ReleaseDateEditor, DueDateEditor, GradingEditor, PublishEditor, AbstractVisibilityEditor, StaffLockEditor,
        ContentVisibilityEditor, VerificationAccessEditor, TimedExaminationPreferenceEditor, AccessEditor;

    CourseOutlineXBlockModal = BaseModal.extend({
        events: _.extend({}, BaseModal.prototype.events, {
            'click .action-save': 'save'
        }),

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'course-outline',
            modalType: 'edit-settings',
            addPrimaryActionButton: true,
            modalSize: 'med',
            viewSpecificClasses: 'confirm',
            editors: []
        }),

        initialize: function() {
            BaseModal.prototype.initialize.call(this);
            this.template = this.loadTemplate('course-outline-modal');
            this.options.title = this.getTitle();
        },

        afterRender: function() {
            BaseModal.prototype.afterRender.call(this);
            this.initializeEditors();
        },

        initializeEditors: function() {
            this.options.editors = _.map(this.options.editors, function(Editor) {
                return new Editor({
                    parentElement: this.$('.modal-section'),
                    model: this.model,
                    xblockType: this.options.xblockType,
                    enable_proctored_exams: this.options.enable_proctored_exams,
                    enable_timed_exams: this.options.enable_timed_exams
                });
            }, this);
        },

        getTitle: function() {
            return '';
        },

        getIntroductionMessage: function() {
            return '';
        },

        getContentHtml: function() {
            return this.template(this.getContext());
        },

        save: function(event) {
            event.preventDefault();
            var requestData = this.getRequestData();
            if (!_.isEqual(requestData, {metadata: {}})) {
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
        getContext: function() {
            return $.extend({
                xblockInfo: this.model,
                introductionMessage: this.getIntroductionMessage(),
                enable_proctored_exams: this.options.enable_proctored_exams,
                enable_timed_exams: this.options.enable_timed_exams
            });
        },

        /**
         * Return request data.
         * @return {Object}
         */
        getRequestData: function() {
            var requestData = _.map(this.options.editors, function(editor) {
                return editor.getRequestData();
            });

            return $.extend.apply(this, [true, {}].concat(requestData));
        }
    });

    SettingsXBlockModal = CourseOutlineXBlockModal.extend({

        getTitle: function() {
            return StringUtils.interpolate(
                gettext('{display_name} Settings'),
                {display_name: this.model.get('display_name')}
            );
        },

        getIntroductionMessage: function() {
            var message = '';
            var tabs = this.options.tabs;
            if (!tabs || tabs.length < 2) {
                message = StringUtils.interpolate(
                    gettext('Change the settings for {display_name}'),
                    {display_name: this.model.get('display_name')}
                );
            }
            return message;
        },

        initializeEditors: function() {
            var tabs = this.options.tabs;
            if (tabs && tabs.length > 0) {
                if (tabs.length > 1) {
                    var tabsTemplate = this.loadTemplate('settings-modal-tabs');
                    HtmlUtils.setHtml(this.$('.modal-section'), HtmlUtils.HTML(tabsTemplate({tabs: tabs})));
                    _.each(this.options.tabs, function(tab) {
                        this.options.editors.push.apply(
                            this.options.editors,
                            _.map(tab.editors, function(Editor) {
                                return new Editor({
                                    parent: this,
                                    parentElement: this.$('.modal-section .' + tab.name),
                                    model: this.model,
                                    xblockType: this.options.xblockType,
                                    enable_proctored_exams: this.options.enable_proctored_exams,
                                    enable_timed_exams: this.options.enable_timed_exams
                                });
                            }, this)
                        );
                    }, this);
                    this.showTab(tabs[0].name);
                } else {
                    this.options.editors = tabs[0].editors;
                    CourseOutlineXBlockModal.prototype.initializeEditors.call(this);
                }
            } else {
                CourseOutlineXBlockModal.prototype.initializeEditors.call(this);
            }
        },

        events: _.extend({}, CourseOutlineXBlockModal.prototype.events, {
            'click .action-save': 'save',
            'click .settings-tab-button': 'handleShowTab'
        }),

        /**
         * Return request data.
         * @return {Object}
         */
        getRequestData: function() {
            var requestData = _.map(this.options.editors, function(editor) {
                return editor.getRequestData();
            });
            return $.extend.apply(this, [true, {}].concat(requestData));
        },

        handleShowTab: function(event) {
            event.preventDefault();
            this.showTab($(event.target).data('tab'));
        },

        showTab: function(tab) {
            this.$('.modal-section .settings-tab-button').removeClass('active');
            this.$('.modal-section .settings-tab-button[data-tab="' + tab + '"]').addClass('active');
            this.$('.modal-section .settings-tab').hide();
            this.$('.modal-section .' + tab).show();
        }
    });


    PublishXBlockModal = CourseOutlineXBlockModal.extend({
        events: _.extend({}, CourseOutlineXBlockModal.prototype.events, {
            'click .action-publish': 'save'
        }),

        initialize: function() {
            CourseOutlineXBlockModal.prototype.initialize.call(this);
            if (this.options.xblockType) {
                this.options.modalName = 'bulkpublish-' + this.options.xblockType;
            }
        },

        getTitle: function() {
            return StringUtils.interpolate(
                gettext('Publish {display_name}'),
                {display_name: this.model.get('display_name')}
            );
        },

        getIntroductionMessage: function() {
            return StringUtils.interpolate(
                gettext('Publish all unpublished changes for this {item}?'),
                {item: this.options.xblockType}
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
            this.parent = this.options.parent;
            this.parentElement = this.options.parentElement;
            this.render();
        },

        render: function() {
            var html = this.template($.extend({}, {
                xblockInfo: this.model,
                xblockType: this.options.xblockType,
                enable_proctored_exam: this.options.enable_proctored_exams,
                enable_timed_exam: this.options.enable_timed_exams
            }, this.getContext()));

            HtmlUtils.setHtml(this.$el, HtmlUtils.HTML(html));
            this.parentElement.append(this.$el);
        },

        getContext: function() {
            return {};
        },

        getRequestData: function() {
            return {};
        }
    });

    BaseDateEditor = AbstractEditor.extend({
        // Attribute name in the model, should be defined in children classes.
        fieldName: null,

        events: {
            'click .clear-date': 'clearValue'
        },

        afterRender: function() {
            AbstractEditor.prototype.afterRender.call(this);
            this.$('input.date').datepicker({'dateFormat': 'm/d/yy'});
            this.$('input.time').timepicker({
                'timeFormat': 'H:i',
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

        getValue: function() {
            return DateUtils.getDate(this.$('#due_date'), this.$('#due_time'));
        },

        clearValue: function(event) {
            event.preventDefault();
            this.$('#due_time, #due_date').val('');
        },

        getRequestData: function() {
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

        afterRender: function() {
            BaseDateEditor.prototype.afterRender.call(this);
            // Store the starting date and time so that we can determine if the user
            // actually changed it when "Save" is pressed.
            this.startingReleaseDate = this.getValue();
        },

        getValue: function() {
            return DateUtils.getDate(this.$('#start_date'), this.$('#start_time'));
        },

        clearValue: function(event) {
            event.preventDefault();
            this.$('#start_time, #start_date').val('');
        },

        getRequestData: function() {
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
        events: {
            'change input.no_special_exam': 'notTimedExam',
            'change input.timed_exam': 'setTimedExam',
            'change input.practice_exam': 'setPracticeExam',
            'change input.proctored_exam': 'setProctoredExam',
            'focusout .field-time-limit input': 'timeLimitFocusout'
        },
        notTimedExam: function(event) {
            event.preventDefault();
            this.$('.exam-options').hide();
            this.$('.field-time-limit input').val('00:00');
        },
        selectSpecialExam: function(showRulesField) {
            this.$('.exam-options').show();
            this.$('.field-time-limit').show();
            if (!this.isValidTimeLimit(this.$('.field-time-limit input').val())) {
                this.$('.field-time-limit input').val('00:30');
            }
            if (showRulesField) {
                this.$('.field-exam-review-rules').show();
            }
            else {
                this.$('.field-exam-review-rules').hide();
            }
        },
        setTimedExam: function(event) {
            event.preventDefault();
            this.selectSpecialExam(false);
        },
        setPracticeExam: function(event) {
            event.preventDefault();
            this.selectSpecialExam(false);
        },
        setProctoredExam: function(event) {
            event.preventDefault();
            this.selectSpecialExam(true);
        },
        timeLimitFocusout: function(event) {
            event.preventDefault();
            var selectedTimeLimit = $(event.currentTarget).val();
            if (!this.isValidTimeLimit(selectedTimeLimit)) {
                $(event.currentTarget).val('00:30');
            }
        },
        afterRender: function() {
            AbstractEditor.prototype.afterRender.call(this);
            this.$('input.time').timepicker({
                'timeFormat': 'H:i',
                'minTime': '00:30',
                'maxTime': '24:00',
                'forceRoundTime': false
            });

            this.setExamType(this.model.get('is_time_limited'), this.model.get('is_proctored_exam'),
                            this.model.get('is_practice_exam'));
            this.setExamTime(this.model.get('default_time_limit_minutes'));

            this.setReviewRules(this.model.get('exam_review_rules'));
        },
        setExamType: function(is_time_limited, is_proctored_exam, is_practice_exam) {
            this.$('.field-time-limit').hide();
            this.$('.field-exam-review-rules').hide();

            if (!is_time_limited) {
                this.$('input.no_special_exam').prop('checked', true);
                return;
            }

            this.$('.field-time-limit').show();

            if (this.options.enable_proctored_exams && is_proctored_exam) {
                if (is_practice_exam) {
                    this.$('input.practice_exam').prop('checked', true);
                } else {
                    this.$('input.proctored_exam').prop('checked', true);
                    this.$('.field-exam-review-rules').show();
                }
            } else {
                // Since we have an early exit at the top of the method
                // if the subsection is not time limited, then
                // here we rightfully assume that it just a timed exam
                this.$('input.timed_exam').prop('checked', true);
            }
        },
        setExamTime: function(value) {
            var time = this.convertTimeLimitMinutesToString(value);
            this.$('.field-time-limit input').val(time);
        },
        setReviewRules: function(value) {
            this.$('.field-exam-review-rules textarea').val(value);
        },
        isValidTimeLimit: function(time_limit) {
            var pattern = new RegExp('^\\d{1,2}:[0-5][0-9]$');
            return pattern.test(time_limit) && time_limit !== '00:00';
        },
        getExamTimeLimit: function() {
            return this.$('.field-time-limit input').val();
        },
        convertTimeLimitMinutesToString: function(timeLimitMinutes) {
            var hoursStr = '' + Math.floor(timeLimitMinutes / 60);
            var actualMinutesStr = '' + (timeLimitMinutes % 60);
            hoursStr = '00'.substring(0, 2 - hoursStr.length) + hoursStr;
            actualMinutesStr = '00'.substring(0, 2 - actualMinutesStr.length) + actualMinutesStr;
            return hoursStr + ':' + actualMinutesStr;
        },
        convertTimeLimitToMinutes: function(time_limit) {
            var time = time_limit.split(':');
            var total_time = (parseInt(time[0]) * 60) + parseInt(time[1]);
            return total_time;
        },
        getRequestData: function() {
            var is_time_limited;
            var is_practice_exam;
            var is_proctored_exam;
            var time_limit = this.getExamTimeLimit();
            var exam_review_rules = this.$('.field-exam-review-rules textarea').val();

            if (this.$('input.no_special_exam').is(':checked')) {
                is_time_limited = false;
                is_practice_exam = false;
                is_proctored_exam = false;
            } else if (this.$('input.timed_exam').is(':checked')) {
                is_time_limited = true;
                is_practice_exam = false;
                is_proctored_exam = false;
            } else if (this.$('input.proctored_exam').is(':checked')) {
                is_time_limited = true;
                is_practice_exam = false;
                is_proctored_exam = true;
            } else if (this.$('input.practice_exam').is(':checked')) {
                is_time_limited = true;
                is_practice_exam = true;
                is_proctored_exam = true;
            }

            return {
                metadata: {
                    'is_practice_exam': is_practice_exam,
                    'is_time_limited': is_time_limited,
                    'exam_review_rules': exam_review_rules,
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

    AccessEditor = AbstractEditor.extend({
        templateName: 'access-editor',
        className: 'edit-settings-access',
        events: {
            'change #prereq': 'handlePrereqSelect',
            'keyup #prereq_min_score': 'validateMinScore'
        },
        afterRender: function() {
            AbstractEditor.prototype.afterRender.call(this);
            var prereq = this.model.get('prereq') || '';
            var prereq_min_score = this.model.get('prereq_min_score') || '';
            this.$('#is_prereq').prop('checked', this.model.get('is_prereq'));
            this.$('#prereq option[value="' + prereq + '"]').prop('selected', true);
            this.$('#prereq_min_score').val(prereq_min_score);
            this.$('#prereq_min_score_input').toggle(prereq.length > 0);
        },
        handlePrereqSelect: function() {
            var showPrereqInput = this.$('#prereq option:selected').val().length > 0;
            this.$('#prereq_min_score_input').toggle(showPrereqInput);
        },
        validateMinScore: function() {
            var minScore = this.$('#prereq_min_score').val().trim();
            var minScoreInt = parseInt(minScore);
            // minScore needs to be an integer between 0 and 100
            if (
                minScore &&
                (
                    typeof(minScoreInt) === 'undefined' ||
                    String(minScoreInt) !== minScore ||
                    minScoreInt < 0 ||
                    minScoreInt > 100
                )
            ) {
                this.$('#prereq_min_score_error').show();
                BaseModal.prototype.disableActionButton.call(this.parent, 'save');
            } else {
                this.$('#prereq_min_score_error').hide();
                BaseModal.prototype.enableActionButton.call(this.parent, 'save');
            }
        },
        getRequestData: function() {
            var minScore = this.$('#prereq_min_score').val();
            if (minScore) {
                minScore = minScore.trim();
            }
            return {
                isPrereq: this.$('#is_prereq').is(':checked'),
                prereqUsageKey: this.$('#prereq option:selected').val(),
                prereqMinScore: minScore
            };
        }
    });

    GradingEditor = AbstractEditor.extend({
        templateName: 'grading-editor',
        className: 'edit-settings-grading',

        afterRender: function() {
            AbstractEditor.prototype.afterRender.call(this);
            this.setValue(this.model.get('format') || 'notgraded');
        },

        setValue: function(value) {
            this.$('#grading_type').val(value);
        },

        getValue: function() {
            return this.$('#grading_type').val();
        },

        getRequestData: function() {
            return {
                'graderType': this.getValue()
            };
        },

        getContext: function() {
            return {
                graderTypes: this.model.get('course_graders')
            };
        }
    });

    PublishEditor = AbstractEditor.extend({
        templateName: 'publish-editor',
        className: 'edit-settings-publish',
        getRequestData: function() {
            return {
                publish: 'make_public'
            };
        }
    });

    AbstractVisibilityEditor = AbstractEditor.extend({
        afterRender: function() {
            AbstractEditor.prototype.afterRender.call(this);
        },

        isModelLocked: function() {
            return this.model.get('has_explicit_staff_lock');
        },

        isAncestorLocked: function() {
            return this.model.get('ancestor_has_staff_lock');
        },

        getContext: function() {
            return {
                hasExplicitStaffLock: this.isModelLocked(),
                ancestorLocked: this.isAncestorLocked()
            };
        }
    });

    StaffLockEditor = AbstractVisibilityEditor.extend({
        templateName: 'staff-lock-editor',
        className: 'edit-staff-lock',
        afterRender: function() {
            AbstractVisibilityEditor.prototype.afterRender.call(this);
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
            if (this.hasChanges()) {
                return {
                    publish: 'republish',
                    metadata: {
                        visible_to_staff_only: this.isLocked() ? true : null
                    }
                };
            } else {
                return {};
            }
        }
    });

    ContentVisibilityEditor = AbstractVisibilityEditor.extend({
        templateName: 'content-visibility-editor',
        className: 'edit-content-visibility',
        events: {
            'change input[name=content-visibility]': 'toggleUnlockWarning'
        },

        modelVisibility: function() {
            if (this.model.get('has_explicit_staff_lock')) {
                return 'staff_only';
            } else if (this.model.get('hide_after_due')) {
                return 'hide_after_due';
            } else {
                return 'visible';
            }
        },

        afterRender: function() {
            AbstractVisibilityEditor.prototype.afterRender.call(this);
            this.setVisibility(this.modelVisibility());
            this.$('input[name=content-visibility]:checked').change();
        },

        setVisibility: function(value) {
            this.$('input[name=content-visibility][value=' + value + ']').prop('checked', true);
        },

        currentVisibility: function() {
            return this.$('input[name=content-visibility]:checked').val();
        },

        hasChanges: function() {
            return this.modelVisibility() !== this.currentVisibility();
        },

        toggleUnlockWarning: function() {
            var warning = this.$('.staff-lock .tip-warning');
            if (warning) {
                var display;
                if (this.currentVisibility() !== 'staff_only') {
                    display = 'block';
                } else {
                    display = 'none';
                }
                $.each(warning, function(_, element) {
                    element.style.display = display;
                });
            }
        },

        getRequestData: function() {
            if (this.hasChanges()) {
                var metadata = {};
                if (this.currentVisibility() === 'staff_only') {
                    metadata.visible_to_staff_only = true;
                    metadata.hide_after_due = null;
                }
                else if (this.currentVisibility() === 'hide_after_due') {
                    metadata.visible_to_staff_only = null;
                    metadata.hide_after_due = true;
                } else {
                    metadata.visible_to_staff_only = null;
                    metadata.hide_after_due = null;
                }

                return {
                    publish: 'republish',
                    metadata: metadata
                };
            }
            else {
                return {};
            }
        },

        getContext: function() {
            return $.extend(
                {},
                AbstractVisibilityEditor.prototype.getContext.call(this),
                {hide_after_due: this.modelVisibility() === 'hide_after_due'}
            );
        }
    });

    VerificationAccessEditor = AbstractEditor.extend({
        templateName: 'verification-access-editor',
        className: 'edit-verification-access',

        // This constant MUST match the group ID
        // defined by VerificationPartitionScheme on the backend!
        ALLOW_GROUP_ID: 1,

        getSelectedPartition: function() {
            var hasRestrictions = $('#verification-access-checkbox').is(':checked'),
                selectedPartitionID = null;

            if (hasRestrictions) {
                selectedPartitionID = $('#verification-partition-select').val();
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
                if (partition.scheme === 'verification') {
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
                    group_access: groupAccess
                }
            } : {};
        },

        getContext: function() {
            var partitions = this.model.get('user_partitions'),
                hasRestrictions = false,
                verificationPartitions = [],
                isSelected = false;

            // Display a simplified version of verified partition schemes.
            // Although there are two groups defined (ALLOW and DENY),
            // we show only the ALLOW group.
            // To avoid searching all the groups, we're assuming that the editor
            // either sets the ALLOW group or doesn't set any groups (implicitly allow all).
            _.each(partitions, function(item) {
                if (item.scheme === 'verification') {
                    isSelected = _.any(_.pluck(item.groups, 'selected'));
                    hasRestrictions = hasRestrictions || isSelected;

                    verificationPartitions.push({
                        'id': item.id,
                        'name': item.name,
                        'selected': isSelected
                    });
                }
            });

            return {
                'hasVerificationRestrictions': hasRestrictions,
                'verificationPartitions': verificationPartitions
            };
        }
    });

    return {
        getModal: function(type, xblockInfo, options) {
            if (type === 'edit') {
                return this.getEditModal(xblockInfo, options);
            } else if (type === 'publish') {
                return this.getPublishModal(xblockInfo, options);
            }
        },

        getEditModal: function(xblockInfo, options) {
            var tabs = [];
            var editors = [];
            if (xblockInfo.isVertical()) {
                editors = [StaffLockEditor];

                if (xblockInfo.hasVerifiedCheckpoints()) {
                    editors.push(VerificationAccessEditor);
                }
            } else {
                tabs = [
                    {
                        name: 'basic',
                        displayName: gettext('Basic'),
                        editors: []
                    },
                    {
                        name: 'advanced',
                        displayName: gettext('Advanced'),
                        editors: []
                    }
                ];
                if (xblockInfo.isChapter()) {
                    tabs[0].editors = [ReleaseDateEditor];
                    tabs[1].editors = [StaffLockEditor];
                } else if (xblockInfo.isSequential()) {
                    tabs[0].editors = [ReleaseDateEditor, GradingEditor, DueDateEditor];
                    tabs[1].editors = [ContentVisibilityEditor];

                    if (options.enable_proctored_exams || options.enable_timed_exams) {
                        tabs[1].editors.push(TimedExaminationPreferenceEditor);
                    }

                    if (typeof(xblockInfo.get('is_prereq')) !== 'undefined') {
                        tabs[1].editors.push(AccessEditor);
                    }
                }
            }

            /* globals course */
            if (course.get('self_paced')) {
                editors = _.without(editors, ReleaseDateEditor, DueDateEditor);
                _.each(tabs, function(tab) {
                    tab.editors = _.without(tab.editors, ReleaseDateEditor, DueDateEditor);
                });
            }

            return new SettingsXBlockModal($.extend({
                tabs: tabs,
                editors: editors,
                model: xblockInfo
            }, options));
        },

        getPublishModal: function(xblockInfo, options) {
            return new PublishXBlockModal($.extend({
                editors: [PublishEditor],
                model: xblockInfo
            }, options));
        }
    };
});
