if (!CMS.Views['Settings']) CMS.Views.Settings = {};

CMS.Views.Settings.Details = CMS.Views.ValidatingView.extend({
    // Model class is CMS.Models.Settings.CourseDetails
    events : {
        "change input" : "updateModel",
        "change textarea" : "updateModel",
        'click .remove-course-syllabus' : "removeSyllabus",
        'click .new-course-syllabus' : 'assetSyllabus',
        'click .remove-course-introduction-video' : "removeVideo",
        'focus #course-overview' : "codeMirrorize",
        'mouseover #timezone' : "updateTime",
        // would love to move to a general superclass, but event hashes don't inherit in backbone :-(
        'focus :input' : "inputFocus",
        'blur :input' : "inputUnfocus"

    },
    initialize : function() {
        this.fileAnchorTemplate = _.template('<a href="<%= fullpath %>"> <i class="icon-file"></i><%= filename %></a>');
        // fill in fields
        this.$el.find("#course-name").val(this.model.get('location').get('name'));
        this.$el.find("#course-organization").val(this.model.get('location').get('org'));
        this.$el.find("#course-number").val(this.model.get('location').get('course'));
        this.$el.find('.set-date').datepicker({ 'dateFormat': 'm/d/yy' });

        var dateIntrospect = new Date();
        this.$el.find('#timezone').html("(" + dateIntrospect.getTimezone() + ")");

        this.listenTo(this.model, 'invalid', this.handleValidationError);
        this.selectorToField = _.invert(this.fieldToSelectorMap);
    },

    render: function() {
        this.setupDatePicker('start_date');
        this.setupDatePicker('end_date');
        this.setupDatePicker('enrollment_start');
        this.setupDatePicker('enrollment_end');

        if (this.model.has('syllabus')) {
            this.$el.find(this.fieldToSelectorMap['syllabus']).html(
                    this.fileAnchorTemplate({
                        fullpath : this.model.get('syllabus'),
                        filename: 'syllabus'}));
            this.$el.find('.remove-course-syllabus').show();
        }
        else {
            this.$el.find('#' + this.fieldToSelectorMap['syllabus']).html("");
            this.$el.find('.remove-course-syllabus').hide();
        }

        this.$el.find('#' + this.fieldToSelectorMap['overview']).val(this.model.get('overview'));
        this.codeMirrorize(null, $('#course-overview')[0]);

        this.$el.find('.current-course-introduction-video iframe').attr('src', this.model.videosourceSample());
        if (this.model.has('intro_video')) {
            this.$el.find('.remove-course-introduction-video').show();
            this.$el.find('#' + this.fieldToSelectorMap['intro_video']).val(this.model.get('intro_video'));
        }
        else this.$el.find('.remove-course-introduction-video').hide();

        this.$el.find('#' + this.fieldToSelectorMap['effort']).val(this.model.get('effort'));

        return this;
    },
    fieldToSelectorMap : {
        'start_date' : "course-start",
        'end_date' : 'course-end',
        'enrollment_start' : 'enrollment-start',
        'enrollment_end' : 'enrollment-end',
        'syllabus' : '.current-course-syllabus .doc-filename',
        'overview' : 'course-overview',
        'intro_video' : 'course-introduction-video',
        'effort' : "course-effort"
    },

    updateTime : function(e) {
        var now = new Date();
        var hours = now.getHours();
        var minutes = now.getMinutes();
        $(e.currentTarget).attr('title', (hours % 12 === 0 ? 12 : hours % 12) + ":" + (minutes < 10 ? "0" : "")  +
                now.getMinutes() + (hours < 12 ? "am" : "pm") + " (current local time)");
    },

    setupDatePicker: function (fieldName) {
        var cacheModel = this.model;
        var div = this.$el.find('#' + this.fieldToSelectorMap[fieldName]);
        var datefield = $(div).find("input:.date");
        var timefield = $(div).find("input:.time");
        var cachethis = this;
        var savefield = function () {
            cachethis.clearValidationErrors();
            var date = datefield.datepicker('getDate');
            if (date) {
                var time = timefield.timepicker("getSecondsFromMidnight");
                if (!time) {
                    time = 0;
                }
                var newVal = new Date(date.getTime() + time * 1000);
                if (!cacheModel.has(fieldName) || cacheModel.get(fieldName).getTime() !== newVal.getTime()) {
                    cacheModel.save(fieldName, newVal);
                }
            }
            else {
                // Clear date (note that this clears the time as well, as date and time are linked).
                // Note also that the validation logic prevents us from clearing the start date
                // (start date is required by the back end).
                cacheModel.save(fieldName, null);
            }
        };

        // instrument as date and time pickers
        timefield.timepicker({'timeFormat' : 'H:i'});
        datefield.datepicker();

        // Using the change event causes savefield to be triggered twice, but it is necessary
        // to pick up when the date is typed directly in the field.
        datefield.change(savefield);
        timefield.on('changeTime', savefield);

        datefield.datepicker('setDate', this.model.get(fieldName));
        if (this.model.has(fieldName)) timefield.timepicker('setTime', this.model.get(fieldName));
    },

    updateModel: function(event) {
        switch (event.currentTarget.id) {
        case 'course-start-date': // handled via onSelect method
        case 'course-end-date':
        case 'course-enrollment-start-date':
        case 'course-enrollment-end-date':
            break;

        case 'course-overview':
            // handled via code mirror
            break;

        case 'course-effort':
            this.saveIfChanged(event);
            break;
        case 'course-introduction-video':
            this.clearValidationErrors();
            var previewsource = this.model.save_videosource($(event.currentTarget).val());
            this.$el.find(".current-course-introduction-video iframe").attr("src", previewsource);
            if (this.model.has('intro_video')) {
                this.$el.find('.remove-course-introduction-video').show();
            }
            else {
                this.$el.find('.remove-course-introduction-video').hide();
            }
            break;

        default:
            break;
        }

    },

    removeSyllabus: function() {
        if (this.model.has('syllabus'))	this.model.save({'syllabus': null});
    },

    assetSyllabus : function() {
        // TODO implement
    },

    removeVideo: function() {
        if (this.model.has('intro_video')) {
            this.model.save_videosource(null);
            this.$el.find(".current-course-introduction-video iframe").attr("src", "");
            this.$el.find('#' + this.fieldToSelectorMap['intro_video']).val("");
            this.$el.find('.remove-course-introduction-video').hide();
        }
    },
    codeMirrors : {},
    codeMirrorize: function (e, forcedTarget) {
        var thisTarget;
        if (forcedTarget) {
            thisTarget = forcedTarget;
            thisTarget.id = $(thisTarget).attr('id');
        } else {
            thisTarget = e.currentTarget;
        }

        if (!this.codeMirrors[thisTarget.id]) {
            var cachethis = this;
            var field = this.selectorToField[thisTarget.id];
            this.codeMirrors[thisTarget.id] = CodeMirror.fromTextArea(thisTarget, {
                mode: "text/html", lineNumbers: true, lineWrapping: true,
                onBlur: function (mirror) {
                    mirror.save();
                    cachethis.clearValidationErrors();
                    var newVal = mirror.getValue();
                    if (cachethis.model.get(field) != newVal) cachethis.model.save(field, newVal);
                }
            });
        }
    }

});

