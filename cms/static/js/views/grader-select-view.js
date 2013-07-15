CMS.Models.AssignmentGrade = Backbone.Model.extend({
	defaults : {
		graderType : null, // the type label (string). May be "Not Graded" which implies None. I'd like to use id but that's ephemeral
		location : null	// A location object
	},
	initialize : function(attrs) {
		if (attrs['assignmentUrl']) {
			this.set('location', new CMS.Models.Location(attrs['assignmentUrl'], {parse: true}));
		}
	},
	parse : function(attrs) {
		if (attrs && attrs['location']) {
			attrs.location = new CMS.Models.Location(attrs['location'], {parse: true});
		}
	},
	urlRoot : function() {
		if (this.has('location')) {
			var location = this.get('location');
			return '/' + location.get('org') + "/" + location.get('course') + '/' + location.get('category') + '/'
			+ location.get('name') + '/gradeas/';
		}
		else return "";
	}
});

CMS.Views.OverviewAssignmentGrader = Backbone.View.extend({
	// instantiate w/ { graders : CourseGraderCollection, el : <the gradable-status div> }
	events : {
		"click .menu-toggle" : "showGradeMenu",
		"click .menu li" : "selectGradeType"
	},
	initialize : function() {
		// call template w/ {assignmentType : formatname, graders : CourseGraderCollection instance }
		this.template = _.template(
				// TODO move to a template file
				'<h4 class="status-label"><%= assignmentType %></h4>' +
				'<a data-tooltip="Mark/unmark this subsection as graded" class="menu-toggle" href="#">' +
					'<% if (!hideSymbol) {%><i class="icon-ok"></i><%};%>' +
				'</a>' +
				'<ul class="menu">' +
					'<% graders.each(function(option) { %>' +
						'<li><a <% if (option.get("type") == assignmentType) {%>class="is-selected" <%}%> href="#"><%= option.get("type") %></a></li>' +
					'<% }) %>' +
					'<li><a class="gradable-status-notgraded" href="#">Not Graded</a></li>' +
				'</ul>');
		this.assignmentGrade = new CMS.Models.AssignmentGrade({
			assignmentUrl : this.$el.closest('.id-holder').data('id'),
			graderType : this.$el.data('initial-status')});
		// TODO throw exception if graders is null
		this.graders = this.options['graders'];
		var cachethis = this;
		// defining here to get closure around this
		this.removeMenu = function(e) {
			e.preventDefault();
			cachethis.$el.removeClass('is-active');
			$(document).off('click', cachethis.removeMenu);
		}
		this.hideSymbol = this.options['hideSymbol'];
		this.render();
	},
	render : function() {
		this.$el.html(this.template({ assignmentType : this.assignmentGrade.get('graderType'), graders : this.graders,
			hideSymbol : this.hideSymbol }));
		if (this.assignmentGrade.has('graderType') && this.assignmentGrade.get('graderType') != "Not Graded") {
			this.$el.addClass('is-set');
		}
		else {
			this.$el.removeClass('is-set');
		}
	},
	showGradeMenu : function(e) {
		e.preventDefault();
		// I sure hope this doesn't break anything but it's needed to keep the removeMenu from activating
		e.stopPropagation();
		// nasty global event trap :-(
		$(document).on('click', this.removeMenu);
		this.$el.addClass('is-active');
	},
	selectGradeType : function(e) {
	      e.preventDefault();

	      this.removeMenu(e);

              var saving = new CMS.Views.Notification.Mini({
                  title: gettext('Saving') + '&hellip;'
              });
              saving.show();

	      // TODO I'm not happy with this string fetch via the html for what should be an id. I'd rather use the id attr
	      // of the CourseGradingPolicy model or null for Not Graded (NOTE, change template's if check for is-selected accordingly)
	      this.assignmentGrade.save(
                  'graderType',
                  $(e.target).text(),
                  {success: function () { saving.hide(); }}
              );

	      this.render();
	}
})
