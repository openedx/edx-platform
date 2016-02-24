define(["js/views/validation", "codemirror", "underscore", "jquery", "jquery.ui", "js/utils/date_utils", "js/models/uploads",
    "js/views/uploads", "js/utils/change_on_enter", "js/views/license", "js/models/license",
    "common/js/components/views/feedback_notification", "jquery.timepicker", "date", "gettext"],
       function(ValidatingView, CodeMirror, _, $, ui, DateUtils, FileUploadModel,
                FileUploadDialog, TriggerChangeEventOnEnter, LicenseView, LicenseModel, NotificationView,
                timepicker, date, gettext) {

var ScheduleView = ValidatingView.extend({
    // Model class is CMS.Models.Settings.CourseSchedule
    events : {
        "input input" : "updateModel",
        "input textarea" : "updateModel",
        // Leaving change in as fallback for older browsers
        "change input" : "updateModel",
        "change textarea" : "updateModel",
        "change select" : "updateModel",
        'mouseover .timezone' : "updateTime",
        // would love to move to a general superclass, but event hashes don't inherit in backbone :-(
        'focus :input' : "inputFocus",
        'blur :input' : "inputUnfocus"
    },

    initialize : function(options) {
        options = options || {};
        this.fileAnchorTemplate = _.template('<a href="<%= fullpath %>"> <i class="icon fa fa-file"></i><%= filename %></a>');
        // fill in fields
        this.$el.find("#course-organization").val(this.model.get('org'));
        this.$el.find("#course-number").val(this.model.get('course_id'));
        this.$el.find("#course-name").val(this.model.get('run'));
        this.$el.find('.set-date').datepicker({ 'dateFormat': 'm/d/yy' });

        this.listenTo(this.model, 'invalid', this.handleValidationError);
        this.listenTo(this.model, 'change', this.showNotificationBar);
        this.selectorToField = _.invert(this.fieldToSelectorMap);
        // handle license separately, to avoid reimplementing view logic
        this.licenseModel = new LicenseModel({"asString": this.model.get('license')});
        this.licenseView = new LicenseView({
            model: this.licenseModel,
            el: this.$("#course-license-selector").get(),
            showPreview: true
        });
        this.listenTo(this.licenseModel, 'change', this.handleLicenseChange);

        if (options.showMinGradeWarning || false) {
            new NotificationView.Warning({
                title: gettext("Course Credit Requirements"),
                message: gettext("The minimum grade for course credit is not set."),
                closeIcon: true
            }).show();
        }
    },

    render: function() {
        this.setupDatePicker('start_date');
        this.setupDatePicker('end_date');
        this.setupDatePicker('enrollment_start');
        this.setupDatePicker('enrollment_end');

        this.$el.find('#' + this.fieldToSelectorMap['effort']).val(this.model.get('effort'));

        var pre_requisite_courses = this.model.get('pre_requisite_courses');
        pre_requisite_courses = pre_requisite_courses.length > 0 ? pre_requisite_courses : '';
        this.$el.find('#' + this.fieldToSelectorMap['pre_requisite_courses']).val(pre_requisite_courses);

        if (this.model.get('entrance_exam_enabled') == 'true') {
            this.$('#' + this.fieldToSelectorMap['entrance_exam_enabled']).attr('checked', this.model.get('entrance_exam_enabled'));
            this.$('.div-grade-requirements').show();
        }
        else {
            this.$('#' + this.fieldToSelectorMap['entrance_exam_enabled']).removeAttr('checked');
            this.$('.div-grade-requirements').hide();
        }
        this.$('#' + this.fieldToSelectorMap['entrance_exam_minimum_score_pct']).val(this.model.get('entrance_exam_minimum_score_pct'));

        var selfPacedButton = this.$('#course-pace-self-paced'),
            instructorPacedButton = this.$('#course-pace-instructor-paced'),
            paceToggleTip = this.$('#course-pace-toggle-tip');
        (this.model.get('self_paced') ? selfPacedButton : instructorPacedButton).attr('checked', true);
        if (this.model.canTogglePace()) {
            selfPacedButton.removeAttr('disabled');
            instructorPacedButton.removeAttr('disabled');
            paceToggleTip.text('');
        }
        else {
            selfPacedButton.attr('disabled', true);
            instructorPacedButton.attr('disabled', true);
            paceToggleTip.text(gettext('Course pacing cannot be changed once a course has started.'));
        }

        this.licenseView.render()

        return this;
    },
    fieldToSelectorMap : {
        'start_date' : "course-start",
        'end_date' : 'course-end',
        'enrollment_start' : 'enrollment-start',
        'enrollment_end' : 'enrollment-end',
        'effort' : "course-effort",
        'pre_requisite_courses': 'pre-requisite-course',
        'entrance_exam_enabled': 'entrance-exam-enabled',
        'entrance_exam_minimum_score_pct': 'entrance-exam-minimum-score-pct'
    },

    updateTime : function(e) {
        var now = new Date(),
            hours = now.getUTCHours(),
            minutes = now.getUTCMinutes(),
            currentTimeText = gettext('%(hours)s:%(minutes)s (current UTC time)');

        $(e.currentTarget).attr('title', interpolate(currentTimeText, {
            'hours': hours,
            'minutes': minutes
        }, true));
    },

    setupDatePicker: function (fieldName) {
        var cacheModel = this.model;
        var div = this.$el.find('#' + this.fieldToSelectorMap[fieldName]);
        var datefield = $(div).find("input.date");
        var timefield = $(div).find("input.time");
        var cachethis = this;
        var setfield = function () {
            var newVal = DateUtils.getDate(datefield, timefield),
                oldTime = new Date(cacheModel.get(fieldName)).getTime();
            if (newVal) {
                if (!cacheModel.has(fieldName) || oldTime !== newVal.getTime()) {
                    cachethis.clearValidationErrors();
                    cachethis.setAndValidate(fieldName, newVal);
                }
            }
            else {
                // Clear date (note that this clears the time as well, as date and time are linked).
                // Note also that the validation logic prevents us from clearing the start date
                // (start date is required by the back end).
                cachethis.clearValidationErrors();
                cachethis.setAndValidate(fieldName, null);
            }
        };

        // instrument as date and time pickers
        timefield.timepicker({'timeFormat' : 'H:i'});
        datefield.datepicker();

        // Using the change event causes setfield to be triggered twice, but it is necessary
        // to pick up when the date is typed directly in the field.
        datefield.change(setfield).keyup(TriggerChangeEventOnEnter);
        timefield.on('changeTime', setfield);
        timefield.on('input', setfield);

        date = this.model.get(fieldName)
        // timepicker doesn't let us set null, so check that we have a time
        if (date) {
            DateUtils.setDate(datefield, timefield, date);
        } // but reset fields either way
        else {
            timefield.val('');
            datefield.val('');
        }
    },

    updateModel: function(event) {
        switch (event.currentTarget.id) {
        case 'course-effort':
            this.setField(event);
            break;
        case 'entrance-exam-enabled':
            if($(event.currentTarget).is(":checked")){
                this.$('.div-grade-requirements').show();
            }else{
                this.$('.div-grade-requirements').hide();
            }
            this.setField(event);
            break;
        case 'entrance-exam-minimum-score-pct':
            // If the val is an empty string then update model with default value.
            if ($(event.currentTarget).val() === '') {
                this.model.set('entrance_exam_minimum_score_pct', this.model.defaults.entrance_exam_minimum_score_pct);
            }
            else {
                this.setField(event);
            }
            break;
        case 'pre-requisite-course':
            var value = $(event.currentTarget).val();
            value = value == "" ? [] : [value];
            this.model.set('pre_requisite_courses', value);
            break;
        case 'course-pace-self-paced':
            // Fallthrough to handle both radio buttons
        case 'course-pace-instructor-paced':
            this.model.set('self_paced', JSON.parse(event.currentTarget.value));
            break;
        default: // Everything else is handled by datepickers and CodeMirror.
            break;
        }
    },

    revertView: function() {
        // Make sure that the CodeMirror instance has the correct
        // data from its corresponding textarea
        var self = this;
        this.model.fetch({
            success: function() {
                self.render();
                _.each(self.codeMirrors, function(mirror) {
                    var ele = mirror.getTextArea();
                    var field = self.selectorToField[ele.id];
                    mirror.setValue(self.model.get(field));
                });
                self.licenseModel.setFromString(self.model.get("license"), {silent: true});
                self.licenseView.render()
            },
            reset: true,
            silent: true});
    },
    setAndValidate: function(attr, value) {
        // If we call model.set() with {validate: true}, model fields
        // will not be set if validation fails. This puts the UI and
        // the model in an inconsistent state, and causes us to not
        // see the right validation errors the next time validate() is
        // called on the model. So we set *without* validating, then
        // call validate ourselves.
        this.model.set(attr, value);
        this.model.isValid();
    },

    showNotificationBar: function() {
        // We always call showNotificationBar with the same args, just
        // delegate to superclass
        ValidatingView.prototype.showNotificationBar.call(this,
                                                          this.save_message,
                                                          _.bind(this.saveView, this),
                                                          _.bind(this.revertView, this));
    },

    handleLicenseChange: function() {
        this.showNotificationBar()
        this.model.set("license", this.licenseModel.toString())
    }
});

return ScheduleView;

}); // end define()
