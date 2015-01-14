var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.pocs = edx.pocs || {};
    edx.pocs.schedule = edx.pocs.schedule || {};

    var syncErrorMessage = gettext("The data could not be saved.");

    var self;

    edx.pocs.schedule.reloadPage = function() {
        location.reload();
    };

    edx.pocs.schedule.UnitModel = Backbone.Model.extend({
        defaults: {
            location: '',
            display_name: '',
            start: null,
            due: null,
            category: '',
            hidden: false,
            children: []
        },

    });

    edx.pocs.schedule.Schedule = Backbone.Collection.extend({

        model: edx.pocs.schedule.UnitModel,
        url: 'poc_schedule'

    });

    edx.pocs.schedule.ScheduleView = Backbone.View.extend({

        initialize: function() {
            _.bindAll(this, 'render');
	    this.schedule_collection = new edx.pocs.schedule.Schedule();
	    this.schedule = {};
	    this.schedule_collection.bind('reset', this.render);
	    this.schedule_collection.fetch({reset: true});
            this.chapter_select = $('form#add-unit select[name="chapter"]'),
            this.sequential_select = $('form#add-unit select[name="sequential"]'),
            this.vertical_select = $('form#add-unit select[name="vertical"]');
            this.dirty = false;
	    self = this;
	    $('#add-all').on('click', function(event) {
	        event.preventDefault();
	        this.schedule_apply(self.schedule, show);
	        self.dirty = true;
	        self.render();
	    });
        },

        render: function() {
	    this.schedule = this.schedule_collection.toJSON();
            this.hidden = this.pruned(this.schedule, function(node) {
              return node.hidden || node.category !== 'vertical'});
            this.showing = this.pruned(this.schedule, function(node) {
              return !node.hidden});
            this.$el.html(schedule_template({chapters: this.showing}));
            $('table.poc-schedule .sequential,.vertical').hide();
            $('table.poc-schedule .toggle-collapse').on('click', this.toggle_collapse);
	    //
	    // Hidden hover fields for empty date fields
	    $('table.poc-schedule .date a').each(function() {
	      if (! $(this).text()) {
		$(this).text('Set date').addClass('empty');
	      }
	    });
	    
	    // Handle date edit clicks
	    $('table.poc-schedule .date a').attr('href', '#enter-date-modal')
	      .leanModal({closeButton: '.close-modal'});
	    $('table.poc-schedule .due-date a').on('click', this.enterNewDate('due'));
	    $('table.poc-schedule .start-date a').on('click', this.enterNewDate('start'));
	    // Click handler for remove all
	    $('table.poc-schedule a#remove-all').on('click', function(event) {
	      event.preventDefault();
	      this.schedule_apply(self.schedule, hide);
	      self.dirty = true;
	      self.render();
	    });

	    // Show or hide form
	    if (this.hidden.length) {
	      // Populate chapters select, depopulate others
	      this.chapter_select.html('')
		.append('<option value="none">'+gettext("Select a chapter")+'...</option>')
		.append(this.schedule_options(this.hidden));
	      this.sequential_select.html('').prop('disabled', true);
	      this.vertical_select.html('').prop('disabled', true);
	      $('form#add-unit').show();
	      $('#all-units-added').hide();
	      $('#add-unit-button').prop('disabled', true);
	    }
	    else {
	      $('form#add-unit').hide();
	      $('#all-units-added').show();
	    }

	    // Add unit handlers
	    this.chapter_select.on('change', function(event) {
	      var chapter_location = self.chapter_select.val();
	      self.vertical_select.html('').prop('disabled', true);
	      if (chapter_location !== 'none') {
		var chapter = self.find_unit(self.hidden, chapter_location);
		self.sequential_select.html('')
		  .append('<option value="all">'+gettext("All subsections")+'</option>')
		  .append(self.schedule_options(chapter.children));
		self.sequential_select.prop('disabled', false);
		$('#add-unit-button').prop('disabled', false);
		self.set_datetime('start', chapter.start);
		self.set_datetime('due', chapter.due);
	      }
	      else {
		self.sequential_select.html('').prop('disabled', true);
	      }
	    });

	    this.sequential_select.on('change', function(event) {
	      var sequential_location = self.sequential_select.val();
	      if (sequential_location !== 'all') {
		var chapter = self.chapter_select.val();
		sequential = self.find_unit(self.hidden, chapter, sequential_location);
		self.vertical_select.html('')
		  .append('<option value="all">'+gettext("All units")+'</option>')
		  .append(schedule_options(sequential.children));
		self.vertical_select.prop('disabled', false);
		self.set_datetime('start', sequential.start);
		self.set_datetime('due', sequential.due);
	      }
	      else {
		self.vertical_select.html('').prop('disabled', true);
	      } 
	    });
	    
	    this.vertical_select.on('change', function(event) {
	      var vertical_location = self.vertical_select.val();
	      if (vertical_location !== 'all') {
		var chapter = chapter_select.val(),
		    sequential = self.sequential_select.val();
		vertical = self.find_unit(
		  self.hidden, chapter, sequential, vertical_location);
		self.set_datetime('start', vertical.start);
		self.set_datetime('due', vertical.due);
	      }
	    });

	    // Add unit handler
	    $('#add-unit-button').on('click', function(event) {
	      event.preventDefault();
	      var chapter = self.chapter_select.val(),
		  sequential = self.sequential_select.val(),
		  vertical = self.vertical_select.val(),
		  units = self.find_lineage(self.schedule,
		    chapter,
		    sequential == 'all' ? null : sequential,
		    vertical == 'all' ? null: vertical),
		  start = self.get_datetime('start'),
		  due = self.get_datetime('due');
	      units.map(show);
	      unit = units[units.length - 1]
	      self.schedule_apply([unit], show);      
	      if (start) unit.start = start;
	      if (due) unit.due = due;
	      self.dirty = true;
	      self.render();
	    });

	    // Remove unit handler
	    $('table.poc-schedule a.remove-unit').on('click', function(event) {
	      var row = $(this).closest('tr'),
		  path = row.data('location').split(' '),
		  unit = self.find_unit(self.schedule, path[0], path[1], path[2]);
	      self.schedule_apply([unit], self.hide);
	      self.dirty = true;
	      self.render(); 
	    });

	    // Show or hide save button
	    if (this.dirty) $('#dirty-schedule').show()
	    else $('#dirty-schedule').hide();

	    // Handle save button
	    $('#dirty-schedule #save-changes').on('click', function(event) {
		event.preventDefault();
		self.save();
	    });

	    $('#ajax-error').hide();

	    return this;
	},

	save: function() {
	    var button = $('#dirty-schedule #save-changes');
	    button.prop('disabled', true).text(gettext("Saving")+'...');
	    
	    $.ajax({
		url: save_url,
		type: 'POST',
		contentType: 'application/json',
		data: JSON.stringify(this.schedule),
		success: function(data, textStatus, jqXHR) {
		  self.schedule = data.schedule;
		  self.dirty = false;
		  self.render();
		  button.prop('disabled', false).text(gettext("Save changes"));
		  
		  // Update textarea with grading policy JSON, since grading policy
		  // may have changed.  
		  $('#grading-policy').text(data.grading_policy);
		},
		error: function(jqXHR, textStatus, error) {
		  console.log(jqXHR.responseText);
		  $('#ajax-error').show();
		  $('#dirty-schedule').hide();
		  $('form#add-unit select,input,button').prop('disabled', true);
		}
	      });
	},

	hide: function(unit) {
	    unit.hidden = true;
	},

        show: function(unit) {
	    unit.hidden = false;
	},

	get_datetime: function(which) {
	    var date = $('form#add-unit input[name=' + which + '_date]').val();
	    var time = $('form#add-unit input[name=' + which + '_time]').val();
	    if (date && time)
	      return date + ' ' + time;
	    return null;
	},

	set_datetime: function(which, value) {
	    var parts = value ? value.split(' ') : ['', ''],
		date = parts[0],
		time = parts[1];
	    $('form#add-unit input[name=' + which + '_date]').val(date);
	    $('form#add-unit input[name=' + which + '_time]').val(time);
	},

	schedule_options: function(nodes) {
	    return nodes.map(function(node) {
	      return $('<option>')
		.attr('value', node.location)
		.text(node.display_name)[0];
	    });
	},

	schedule_apply: function(nodes, f) {
	    nodes.map(function(node) {
	      f(node);
	      if (node.children !== undefined) self.schedule_apply(node.children, f);
	    });
	},

	pruned: function(tree, filter) {
	    return tree.filter(filter)
	      .map(function(node) {
		var copy = {};
		$.extend(copy, node);
		if (node.children) copy.children = self.pruned(node.children, filter);
		return copy;
	      })
	      .filter(function(node) {
		return node.children === undefined || node.children.length;
	      });
	},

	toggle_collapse: function(event) {
	    event.preventDefault();
	    var row = $(this).closest('tr');
	    var children = self.get_children(row);

	    if (row.is('.expanded')) {
	      $(this).removeClass('icon-caret-down').addClass('icon-caret-right');
	      row.removeClass('expanded').addClass('collapsed');
	      children.hide(); 
	    }

	    else {
	      $(this).removeClass('icon-caret-right').addClass('icon-caret-down');
	      row.removeClass('collapsed').addClass('expanded');
	      children.filter('.collapsed').each(function() {
		children = children.not(self.get_children(this));
	      });
	      children.show(); 
	    }
	},

	enterNewDate: function(what) {
	    return function(event) {
	      var row = $(this).closest('tr');
	      var modal = $('#enter-date-modal')
		.data('what', what)
		.data('location', row.data('location'));
	      modal.find('h2').text(
		  what == 'due' ? gettext("Enter Due Date") : 
		      gettext("Enter Start Date"));
	      modal.find('label').text(row.find('td:first').text());

	      var path = row.data('location').split(' '),
		  unit = self.find_unit(self.schedule, path[0], path[1], path[2]),
		  parts = unit[what] ? unit[what].split(' ') : ['', ''],
		  date = parts[0],
		  time = parts[1];

	      modal.find('input[name=date]').val(date);
	      modal.find('input[name=time]').val(time);

	      modal.find('form').off('submit').on('submit', function(event) {
		event.preventDefault();
		var date = $(this).find('input[name=date]').val(),
		    time = $(this).find('input[name=time]').val();
		var valid_date = new Date(date);
		if (isNaN(valid_date.valueOf())) {
		  alert('Please enter a valid date');
		  return;
		}
		var valid_time = /^\d{1,2}:\d{2}?$/;
		if (!time.match(valid_time)) {
		  alert('Please enter a valid time');
		  return;
		}
		unit[what] = date + ' ' + time;
		modal.find('.close-modal').click();
		self.dirty = true;
		self.render();
	      });
	    }
	},

	find_unit: function(tree, chapter, sequential, vertical) {
	    var units = self.find_lineage(tree, chapter, sequential, vertical);
	    return units[units.length -1];
	},

	find_lineage: function(tree, chapter, sequential, vertical) {
	    function find_in(seq, location) {
	      for (var i = 0; i < seq.length; i++)
		if (seq[i].location === location)
		  return seq[i];
	    }

	    var units = [],
		unit = find_in(tree, chapter);
	    units[units.length] = unit;
	    if (sequential) {
	      units[units.length] = unit = find_in(unit.children, sequential);
	      if (vertical) 
		units[units.length] = unit = find_in(unit.children, vertical);
	    }

	    return units;
	},

	get_children: function(row) {
	    var depth = $(row).data('depth');
	    return $(row).nextUntil(
	      $(row).siblings().filter(function() {
		return $(this).data('depth') <= depth;
	      })
	    );
	}

    });

	    edx.pocs.schedule.XScheduleView = Backbone.View.extend({

		events: {
		    'submit': 'submit',
		    'change': 'change'
		},

		initialize: function() {
		    _.bindAll(this, 'render', 'change', 'submit', 'invalidProfile', 'invalidPreference', 'error', 'sync', 'clearStatus');
		    
		    this.scheduleModel = new edx.pocs.schedule.ProfileModel();
		    this.scheduleModel.on('invalid', this.invalidProfile);
		    this.scheduleModel.on('error', this.error);
		    this.scheduleModel.on('sync', this.sync);

		    this.preferencesModel = new edx.pocs.schedule.PreferencesModel();
		    this.preferencesModel.on('invalid', this.invalidPreference);
		    this.preferencesModel.on('error', this.error);
		    this.preferencesModel.on('sync', this.sync);
		},

		render: function() {
		    this.$el.html(_.template($('#schedule-tpl').html()));

		    this.$nameField = $('#schedule-name', this.$el);
		    this.$nameStatus = $('#schedule-name-status', this.$el);
		    
		    this.$languageChoices = $('#preference-language', this.$el);
		    this.$languageStatus = $('#preference-language-status', this.$el);

		    this.$submitStatus = $('#submit-status', this.$el);

		    var self = this;
		    $.getJSON('preferences/languages')
			.done(function(json) {
			    /** Asynchronously populate the language choices. */
			    self.$languageChoices.html(_.template($('#languages-tpl').html(), {languageInfo: json}));
			})
			.fail(function() {
			    self.$languageStatus
				.addClass('language-list-error')
				.text(gettext("We couldn't populate the list of language choices."));
			});

		    return this;
		},

		change: function() {
		    this.scheduleModel.set({
			fullName: this.$nameField.val()
		    });

		    this.preferencesModel.set({
			language: this.$languageChoices.val()
		    });
		},

		submit: function(event) {
		    event.preventDefault();
		    this.clearStatus();
		    this.scheduleModel.save();
		    this.preferencesModel.save();
		},

		invalidProfile: function(model) {
		    var errors = model.validationError;
		    if (errors.hasOwnProperty('fullName')) {
			this.$nameStatus
			    .addClass('validation-error')
			    .text(errors.fullName);
		    }
		},

		invalidPreference: function(model) {
		    var errors = model.validationError;
		    if (errors.hasOwnProperty('language')) {
			this.$languageStatus
			    .addClass('validation-error')
			    .text(errors.language);
		    }
		},

		error: function(error) {
		    this.$submitStatus
			.addClass('error')
			.text(error);
		},

		sync: function() {
		    this.$submitStatus
			.addClass('success')
			.text(gettext("Saved"));
		},

		clearStatus: function() {
		    this.$nameStatus
			.removeClass('validation-error')
			.text("");

		    this.$languageStatus
			.removeClass('validation-error')
			.text("");

		    this.$submitStatus
			.removeClass('error')
			.text("");
		}
	    });

	})(jQuery, _, Backbone, gettext);




