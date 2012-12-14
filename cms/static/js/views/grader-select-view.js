CMS.Models.AssignmentGrade = Backbone.Model.extend({
	idAttribute : "cid",	// not sure if this is kosher
	defaults : {
		grader-type : null, // the type label (string). May be "Not Graded" which implies None. I'd like to use id but that's ephemeral
		location : null	// A location object
	},
	initialize : function(attrs) {
		if (attrs['assignment-url']) {
			this.set('location') = new CMS.Models.Location(attrs['assignment-url'], {parse: true});
		}
	},
	parse : function(attrs) {
		if (attrs['location']) {
			attrs.location = new CMS.Models.Location(attrs['location'], {parse: true});
		}
	}
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
		"click .menu" : "selectGradeType"
	},
	initialize : function() {
		// call template w/ {assignment-type : formatname, graders : CourseGraderCollection instance }
		this.template = _.template(
				'<h4 class="status-label"><%= assignment-type %></h4>' +
				'<a data-tooltip="Mark/unmark this section as graded" class="menu-toggle" href="#">' +
					'<span class="ss-icon ss-standard">&#x2713;</span>' +
				'</a>' +
				'<ul class="menu">' + 
					'<% graders.each(function(option) { %>' +
						'<li><a <% if (option.get("type") == assignment-type) {%>class="is-selected" <%}%> href="#"><%= option.get("type") %></a></li>' +
					'<% }) %>'
					'<li><a class="gradable-status-notgraded" href="#">Not Graded</a></li>'
				'</ul>');
		this.assignmentGrade = new CMS.Models.AssignmentGrade({
			assignment-url : this.$el.closest('section.branch').data('id'), 
			grader-type : this.$el.data('initial-status')});
		this.render();
	},
	render : function() {
		this.$el.html(this.template({ assignment-type : this.assignmentGrade.get('grader-type'), graders : this.graders }));
		if (this.assignmentGrade.has('grader-type') && assignmentGrade.get('grader-type') != "Not Graded") {
			this.$el.addClass('is-set');
		}
		else {
			this.$el.removeClass('is-set');
		}
	},
	showGradeMenu : function(e) {
		e.preventDefault();
		this.$el.toggleClass('is-active');
	},
	selectGradeType : function(e) {
	      e.preventDefault();

	      // TODO I'm not happy with this string fetch via the html for what should be an id. I'd rather use the id attr
	      // of the CourseGradingPolicy model or null for Not Graded (NOTE, change template's if check for is-selected accordingly)
	      this.assignmentGrade.save('grader-type', $(e.target).html());
	      
	      this.render();
	}
})