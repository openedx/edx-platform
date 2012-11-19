CMS.Views.Settings.Main = Backbone.View.extend({
	// Model class is CMS.Models.Settings.CourseSettings
	// allow navigation between the tabs
	events: {
		'click .settings-page-menu a': "showSettingsTab"
	},
	initialize: function() {
		// load templates
	},
	render: function() {
		// create any necessary subviews and put them onto the page
	},
	
	currentTab: null, 
		
	showSettingsTab: function(e) {
		this.currentTab = $(e.target).attr('data-section');
		$('.settings-page-section > section').hide();
		$('.settings-' + this.currentTab).show();
		$('.settings-page-menu .is-shown').removeClass('is-shown');
		$(e.target).addClass('is-shown');
		// fetch model for the tab if not loaded already
		if (!this.model.has(this.currentTab)) {
			// TODO disable screen until fetch completes?
			this.model.retrieve(this.currentTab, function() { this.render(); });
		}
	}

})