CMS.Views.Settings.Main = Backbone.View.extend({
	// Model class is CMS.Models.Settings.CourseSettings
	// allow navigation between the tabs
	events: {
		'click .settings-page-menu a': "showSettingsTab",
	},
	
	currentTab: null, 
	subviews: {},	# indexed by tab name

	initialize: function() {
		// load templates
		this.currentTab = this.$el.find('.settings-page-menu .is-shown').attr('data-section');
		// create the initial subview
		this.subviews[this.currentTab] = this.createSubview();
			
		// fill in fields
		this.$el.find("#course-name").val(this.model.get('courseLocation').get('name'));
		this.$el.find("#course-organization").val(this.model.get('courseLocation').get('org'));
		this.$el.find("#course-number").val(this.model.get('courseLocation').get('course'));
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
		}
		else this.callRenderFunction();
		
		return this;
	},
	
	createSubview: function() {
		switch (this.currentTab) {
		case 'details':
			return new CMS.Views.Settings.Details({
				el: this.$el.find('.settings-' + this.currentTab),
				model: this.model.get(this.currentTab);
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
		'click .remove-course-syllabus' : "removeSyllabus",
		'click .new-course-syllabus' : 'assetSyllabus',
		'click .remove-course-introduction-video' : "removeVideo",
		'click .new-course-introduction-video' : 'assetVideo',
	},
	initialize : function() {
		// TODO move the html frag to a loaded asset
		this.fileAnchorTemplate = _.template('<a href="<%= fullpath %>"> <i class="ss-icon ss-standard">&#x1F4C4;</i><%= filename %></a>');
		// Save every change as it occurs. This may be too noisy!!! If not every change, then need sophisticated logic.
		this.model.on('change', this.model.save);
	},
	
	render: function() {
		if (this.model.has('start_date')) this.$el.find('#course-start-date').datepicker('setDate', this.model.get('start_date'));
		if (this.model.has('end_date')) this.$el.find('#course-end-date').datepicker('setDate', this.model.get('end_date'));
		if (this.model.has('enrollment_start')) this.$el.find('#course-enrollment-start').datepicker('setDate', this.model.get('enrollment_start'));
		if (this.model.has('enrollment_end')) this.$el.find('#course-enrollment-end').datepicker('setDate', this.model.get('enrollment_end'));
		
		if (this.model.has('syllabus')) {
			this.$el.find('.current-course-syllabus .doc-filename').html(
					this.fileAnchorTemplate({
						fullpath : this.model.get('syllabus'),
						filename: 'syllabus'}));
			this.$el.find('.remove-course-syllabus').show();
		}
		else this.$el.find('.remove-course-syllabus').hide();
		
		if (this.model.has('overview'))
			this.$el.find('#course-overview').text(this.model.get('overview'));
		
		if (this.model.has('intro_video')) {
			this.$el.find('.current-course-introduction-video iframe').attr('src', this.model.get('intro_video'));
			this.$el.find('.remove-course-introduction-video').show();
		}
		else this.$el.find('.remove-course-introduction-video').hide();
	},
	
	updateModel: function(event) {
		// figure out which field
		switch (event.currentTarget.id) {
		case 'course-start-date':
			var val = $(event.currentTarget).datepicker('getDate');
			this.model.set('start_date', val);
			break;
		case 'course-end-date':
			this.model.set('end_date', $(event.currentTarget).datepicker('getDate'));
			break;
		case 'course-enrollment-start-date':
			this.model.set('enrollment_start', $(event.currentTarget).datepicker('getDate'));
			break;
		case 'course-enrollment-end-date':
			this.model.set('enrollment_end', $(event.currentTarget).datepicker('getDate'));
			break;

		case 'course-overview':
			this.model.set('overview', $(event.currentTarget).text());
			break;

		default:
			break;
		}
	},
	
	removeSyllabus: function() {
		if (this.model.has('syllabus'))	this.model.set({'syllabus': null});
	},
	
	assetSyllabus : function() {
		// TODO implement
	},
	
	removeVideo: function() {
		if (this.model.has('intro_video'))	this.model.set({'intro_video': null});
	},
	
	assetVideo : function() {
		// TODO implement
	}
});