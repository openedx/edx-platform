var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.ccx = edx.ccx || {};
    edx.ccx.schedule = edx.ccx.schedule || {};

    var self;

    edx.ccx.schedule.reloadPage = function() {
        location.reload();
    };

    edx.ccx.schedule.UnitModel = Backbone.Model.extend({
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

    edx.ccx.schedule.Schedule = Backbone.Collection.extend({

        model: edx.ccx.schedule.UnitModel,
        url: 'ccx_schedule'

    });

    edx.ccx.schedule.ScheduleView = Backbone.View.extend({

        initialize: function() {
            _.bindAll(this, 'render');
	    this.schedule_collection = new edx.ccx.schedule.Schedule();
	    this.schedule = {};
	    this.schedule_collection.bind('reset', this.render);
	    this.schedule_collection.fetch({reset: true});
            this.chapter_select = $('form#add-unit select[name="chapter"]');
            this.sequential_select = $('form#add-unit select[name="sequential"]');
            this.vertical_select = $('form#add-unit select[name="vertical"]');
            this.dirty = false;
	    self = this;
	    $('#add-all').on('click', function(event) {
	        event.preventDefault();
	        self.schedule_apply(self.schedule, self.show);
	        self.dirty = true;
		self.schedule_collection.set(self.schedule);
	        self.render();
	    });

	    // Add unit handlers
	    this.chapter_select.on('change', function() {
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

	    this.sequential_select.on('change', function() {
	      var sequential_location = self.sequential_select.val();
	      if (sequential_location !== 'all') {
		var chapter = self.chapter_select.val(),
		sequential = self.find_unit(self.hidden, chapter, sequential_location);
		self.vertical_select.html('')
		  .append('<option value="all">'+gettext("All units")+'</option>')
		  .append(self.schedule_options(sequential.children));
		self.vertical_select.prop('disabled', false);
		self.set_datetime('start', sequential.start);
		self.set_datetime('due', sequential.due);
	      }
	      else {
		self.vertical_select.html('').prop('disabled', true);
	      } 
	    });
	    
	    this.vertical_select.on('change', function() {
	      var vertical_location = self.vertical_select.val();
	      if (vertical_location !== 'all') {
		var chapter = self.chapter_select.val(),
		    sequential = self.sequential_select.val();
		var vertical = self.find_unit(
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
		    sequential === 'all' ? null : sequential,
		    vertical === 'all' ? null: vertical),
		  start = self.get_datetime('start'),
		  due = self.get_datetime('due');
	      units.map(self.show);
	      var unit = units[units.length - 1];
	      self.schedule_apply([unit], self.show);      
	      if (unit !== undefined && start) { unit.start = start; }
	      if (unit !== undefined && due) { unit.due = due; }
	      self.schedule_collection.set(self.schedule);
	      self.dirty = true;
	      self.render();
	    });

	    // Handle save button
	    $('#dirty-schedule #save-changes').on('click', function(event) {
		event.preventDefault();
		self.save();
	    });

        },

        render: function() {
	    self.schedule = this.schedule_collection.toJSON();
            self.hidden = this.pruned(self.schedule, function(node) {
              return node.hidden || node.category !== 'vertical';});
            this.showing = this.pruned(self.schedule, function(node) {
              return !node.hidden;});
            this.$el.html(schedule_template({chapters: this.showing}));
            $('table.ccx-schedule .sequential,.vertical').hide();
            $('table.ccx-schedule .toggle-collapse').on('click', this.toggle_collapse);
	    //
	    // Hidden hover fields for empty date fields
	    $('table.ccx-schedule .date a').each(function() {
	      if (! $(this).text()) {
		$(this).text('Set date').addClass('empty');
	      }
	    });
	    
	    // Handle date edit clicks
	    $('table.ccx-schedule .date a').attr('href', '#enter-date-modal')
	      .leanModal({closeButton: '.close-modal'});
	    $('table.ccx-schedule .due-date a').on('click', this.enterNewDate('due'));
	    $('table.ccx-schedule .start-date a').on('click', this.enterNewDate('start'));
	    // Click handler for remove all
	    $('table.ccx-schedule a#remove-all').on('click', function(event) {
	      event.preventDefault();
	      self.schedule_apply(self.schedule, self.hide);
	      self.dirty = true;
	      self.schedule_collection.set(self.schedule);
	      self.render();
	    });
	    // Remove unit handler
	    $('table.ccx-schedule a.remove-unit').on('click', function() {
	      var row = $(this).closest('tr'),
		  path = row.data('location').split(' '),
		  unit = self.find_unit(self.schedule, path[0], path[1], path[2]);
	      self.schedule_apply([unit], self.hide);
	      self.schedule_collection.set(self.schedule);
	      self.dirty = true;
	      self.render(); 
	    });


	    // Show or hide form
	    if (this.hidden.length) {
	      // Populate chapters select, depopulate others
	      this.chapter_select.html('')
		.append('<option value="none">'+gettext("Select a chapter")+'...</option>')
		.append(self.schedule_options(this.hidden));
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

	    // Show or hide save button
	    if (this.dirty) {$('#dirty-schedule').show();}
	    else {$('#dirty-schedule').hide();}

	    $('#ajax-error').hide();

	    return this;
	},

	save: function() {
	    self.schedule_collection.set(self.schedule);
	    var button = $('#dirty-schedule #save-changes');
	    button.prop('disabled', true).text(gettext("Saving")+'...');
	    
	    $.ajax({
		url: save_url,
		type: 'POST',
		contentType: 'application/json',
		data: JSON.stringify(self.schedule),
		success: function(data) {
		  self.dirty = false;
		  self.render();
		  button.prop('disabled', false).text(gettext("Save changes"));
		  
		  // Update textarea with grading policy JSON, since grading policy
		  // may have changed.  
		  $('#grading-policy').text(data.grading_policy);
		},
		error: function(jqXHR) {
		  console.log(jqXHR.responseText);
		  $('#ajax-error').show();
		  $('#dirty-schedule').hide();
		  $('form#add-unit select,input,button').prop('disabled', true);
		  button.prop('disabled', false).text(gettext("Save changes"));
		}
	      });
	},

	hide: function(unit) {
	    if (unit !== undefined) {
	        unit.hidden = true;
	    }
	},

        show: function(unit) {
	    if (unit !== undefined) {
	        unit.hidden = false;
	    }
	},

	get_datetime: function(which) {
	    var date = $('form#add-unit input[name=' + which + '_date]').val();
	    var time = $('form#add-unit input[name=' + which + '_time]').val();
	    if (date && time) {
	      return date + ' ' + time; }
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
	      if (node !== undefined && node.children !== undefined) { self.schedule_apply(node.children, f); }
	    });
	},

	pruned: function(tree, filter) {
	    return tree.filter(filter)
	      .map(function(node) {
		var copy = {};
		$.extend(copy, node);
		if (node.children) {copy.children = self.pruned(node.children, filter);}
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
	      $(this).removeClass('fa-caret-down').addClass('fa-caret-right');
	      row.removeClass('expanded').addClass('collapsed');
	      children.hide(); 
	    }

	    else {
	      $(this).removeClass('fa-caret-right').addClass('fa-caret-down');
	      row.removeClass('collapsed').addClass('expanded');
	      children.filter('.collapsed').each(function() {
		children = children.not(self.get_children(this));
	      });
	      children.show(); 
	    }
	},

	enterNewDate: function(what) {
	    return function() {
	      var row = $(this).closest('tr');
	      var modal = $('#enter-date-modal')
		.data('what', what)
		.data('location', row.data('location'));
	      modal.find('h2').text(
		  what === 'due' ? gettext("Enter Due Date") : 
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
		if (what === 'start') {
		    unit.start = date + ' ' + time;
		} else {
		    unit.due = date + ' ' + time;
		}
		modal.find('.close-modal').click();
		self.dirty = true;
		self.schedule_collection.set(self.schedule);
		self.render();
	      });
	    };
	},

	find_unit: function(tree, chapter, sequential, vertical) {
	    var units = self.find_lineage(tree, chapter, sequential, vertical);
	    return units[units.length -1];
	},

	find_lineage: function(tree, chapter, sequential, vertical) {
	    function find_in(seq, location) {
	      for (var i = 0; i < seq.length; i++) {
		if (seq[i].location === location) {
		  return seq[i];}
	    }}

	    var units = [],
		unit = find_in(tree, chapter);
	    units[units.length] = unit;
	    if (sequential) {
	      units[units.length] = unit = find_in(unit.children, sequential);
	      if (vertical) {
		units[units.length] = unit = find_in(unit.children, vertical);}
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

})(jQuery, _, Backbone, gettext);




