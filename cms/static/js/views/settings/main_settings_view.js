if (!CMS.Views['Settings']) CMS.Views.Settings = new Object();

CMS.Views.Settings.Main = Backbone.View.extend({
	// Model class is CMS.Models.Settings.CourseSettings
	// allow navigation between the tabs
	events: {
		'click .settings-page-menu a': "showSettingsTab",
	},
	
	currentTab: null, 
	subviews: {},	// indexed by tab name

	initialize: function() {
		// load templates
		this.currentTab = this.$el.find('.settings-page-menu .is-shown').attr('data-section');
		// create the initial subview
		this.subviews[this.currentTab] = this.createSubview();
			
		// fill in fields
		this.$el.find("#course-name").val(this.model.get('courseLocation').get('name'));
		this.$el.find("#course-organization").val(this.model.get('courseLocation').get('org'));
		this.$el.find("#course-number").val(this.model.get('courseLocation').get('course'));
		this.$el.find('.set-date').datepicker({ 'dateFormat': 'm/d/yy' });
		this.$el.find(":input, textarea").focus(function() {
	      $("label[for='" + this.id + "']").addClass("is-focused");
	    }).blur(function() {
	      $("label").removeClass("is-focused");
	    });
		this.render();
	},
	
	render: function() {
		
		// create any necessary subviews and put them onto the page
		if (!this.model.has(this.currentTab)) {
			// TODO disable screen until fetch completes?
			this.model.retrieve(this.currentTab, function() {
				this.subviews[this.currentTab] = this.createSubview();
				this.subviews[this.currentTab].render();
			});
			}
		else this.subviews[this.currentTab].render();
		
		return this;
	},
	
	createSubview: function() {
		switch (this.currentTab) {
		case 'details':
			return new CMS.Views.Settings.Details({
				el: this.$el.find('.settings-' + this.currentTab),
				model: this.model.get(this.currentTab)
			});
			break;
		case 'faculty':
			break;
		case 'grading':
			break;
		case 'problems':
			break;
		case 'discussions':
			break;
		}
	},
	
	showSettingsTab: function(e) {
		this.currentTab = $(e.target).attr('data-section');
		$('.settings-page-section > section').hide();
		$('.settings-' + this.currentTab).show();
		$('.settings-page-menu .is-shown').removeClass('is-shown');
		$(e.target).addClass('is-shown');
		// fetch model for the tab if not loaded already
		this.render();
	}

});

CMS.Views.Settings.Details = Backbone.View.extend({
	// Model class is CMS.Models.Settings.CourseDetails
	events : {
		"blur input" : "updateModel",
		"blur textarea" : "updateModel",
		'click .remove-course-syllabus' : "removeSyllabus",
		'click .new-course-syllabus' : 'assetSyllabus',
		'click .remove-course-introduction-video' : "removeVideo"
	},
	initialize : function() {
		// TODO move the html frag to a loaded asset
		this.fileAnchorTemplate = _.template('<a href="<%= fullpath %>"> <i class="ss-icon ss-standard">&#x1F4C4;</i><%= filename %></a>');
		this.errorTemplate = _.template('<span class="message-error"><%= message %></span>');
		this.model.on('error', this.handleValidationError, this);
	},
	
	render: function() {
		this.setupDatePicker('start_date')
		this.setupDatePicker('end_date')
		this.setupDatePicker('enrollment_start')
		this.setupDatePicker('enrollment_end')
		
		if (this.model.has('syllabus')) {
			this.$el.find(this.fieldToSelectorMap['syllabus']).html(
					this.fileAnchorTemplate({
						fullpath : this.model.get('syllabus'),
						filename: 'syllabus'}));
			this.$el.find('.remove-course-syllabus').show();
		}
		else {
			this.$el.find(this.fieldToSelectorMap['syllabus']).html("");
			this.$el.find('.remove-course-syllabus').hide();
		}
		
		this.$el.find(this.fieldToSelectorMap['overview']).val(this.model.get('overview'));
		
		this.$el.find('.current-course-introduction-video iframe').attr('src', this.model.videosourceSample());
		if (this.model.has('intro_video')) {
			this.$el.find('.remove-course-introduction-video').show();
			this.$el.find(this.fieldToSelectorMap['intro_video']).val(this.model.getVideoSource());
		}
		else this.$el.find('.remove-course-introduction-video').hide();
		
		this.$el.find(this.fieldToSelectorMap['effort']).val(this.model.get('effort'));
		
		return this;
	},
	fieldToSelectorMap : {
		'start_date' : "#course-start",
		'end_date' : '#course-end',
		'enrollment_start' : '#enrollment-start',
		'enrollment_end' : '#enrollment-end',
		'syllabus' : '.current-course-syllabus .doc-filename',
		'overview' : '#course-overview',
		'intro_video' : '#course-introduction-video',
		'effort' : "#course-effort"
	},
	
	_cacheValidationErrors : null,
	handleValidationError : function(model, error) {
		this._cacheValidationErrors = error;
		// error is object w/ fields and error strings
		for (var field in error) {
			var ele = this.$el.find(this.fieldToSelectorMap[field]); 
			if ($(ele).is('div')) {
				// put error on the contained inputs
				$(ele).find('input, textarea').addClass('error');
			}
			else $(ele).addClass('error');
			$(ele).parent().append(this.errorTemplate({message : error[field]}));
		}
	},
	
	clearValidationErrors : function() {
		if (this._cacheValidationErrors == null) return;
		// error is object w/ fields and error strings
		for (var field in this._cacheValidationErrors) {
			var ele = this.$el.find(this.fieldToSelectorMap[field]); 
			if ($(ele).is('div')) {
				// put error on the contained inputs
				$(ele).find('input, textarea').removeClass('error');
			}
			else $(ele).removeClass('error');
			$(ele).nextAll('.message-error').remove();
		}
		this._cacheValidationErrors = null;
	},
	
	setupDatePicker : function(fieldName) {
		var cacheModel = this.model;
		var div = this.$el.find(this.fieldToSelectorMap[fieldName]);
		var datefield = $(div).find(".date");
		var timefield = $(div).find(".time");
		var savefield = function() { 
			cacheModel.save(fieldName, new Date(datefield.datepicker('getDate').getTime() 
					+ timefield.timepicker("getSecondsFromMidnight") * 1000)); 
		};
		
		// instrument as date and time pickers
		timefield.timepicker();
		
		// FIXME being called 2x on each change. Was trapping datepicker onSelect b4 but change to datepair broke that
		datefield.datepicker({ onSelect : savefield });
		timefield.on('changeTime', savefield);
		
		datefield.datepicker('setDate', this.model.get(fieldName));
		timefield.timepicker('setTime', this.model.get(fieldName));
	},
	
	updateModel: function(event) {
		this.clearValidationErrors();

		switch (event.currentTarget.id) {
		case 'course-start-date': // handled via onSelect method
		case 'course-end-date':
		case 'course-enrollment-start-date':
		case 'course-enrollment-end-date':
			break;

		case 'course-overview':
			this.model.save('overview', $(event.currentTarget).val());
			break;

		case 'course-effort':
			this.model.save('effort', $(event.currentTarget).val());
			break;
		case 'course-introduction-video':
			var previewsource = this.model.save_videosource($(event.currentTarget).val());
			this.$el.find(".current-course-introduction-video iframe").attr("src", previewsource);
			break
			
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
			this.$el.find(this.fieldToSelectorMap['intro_video']).val("");
		}
	}
	
});