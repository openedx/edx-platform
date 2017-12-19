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
        }
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

      // By default input date and time fileds are disable.
            self.disableFields($('.ccx_due_date_time_fields'));
            self.disableFields($('.ccx_start_date_time_fields'));
      // Add unit handlers
            this.chapter_select.on('change', function() {
                var chapter_location = self.chapter_select.val();
                self.vertical_select.html('').prop('disabled', true);
                if (chapter_location !== 'none') {
                    var chapter = self.find_unit(self.hidden, chapter_location);
                    self.sequential_select.html('')
          .append('<option value="all">' + gettext('All subsections') + '</option>')
          .append(self.schedule_options(chapter.children));
                    self.sequential_select.prop('disabled', false);
                    $('#add-unit-button').prop('disabled', false);
          // When a chapter is selected, start date fields are enabled and due date
          // fields are disabled because due dates are not applicable on a chapter.
                    self.disableFields($('.ccx_due_date_time_fields'));
                    self.enableFields($('.ccx_start_date_time_fields'));
                } else {
                    self.sequential_select.html('').prop('disabled', true);
          // When no chapter is selected, all date fields are disabled.
                    self.disableFields($('.ccx_due_date_time_fields'));
                    self.disableFields($('.ccx_start_date_time_fields'));
                }
            });

            this.sequential_select.on('change', function() {
                var sequential_location = self.sequential_select.val();
                if (sequential_location !== 'all') {
                    var chapter = self.chapter_select.val(),
                        sequential = self.find_unit(self.hidden, chapter, sequential_location);
                    self.vertical_select.html('')
           .append('<option value="all">' + gettext('All units') + '</option>')
           .append(self.schedule_options(sequential.children));
                    self.vertical_select.prop('disabled', false);
                    self.set_datetime('start', sequential.start);
                    self.set_datetime('due', sequential.due);
           // When a subsection (aka sequential) is selected,
           // both start and due date fields are enabled.
                    self.enableFields($('.ccx_due_date_time_fields'));
                    self.enableFields($('.ccx_start_date_time_fields'));
                } else {
           // When "All subsections" is selected, all date fields are disabled.
                    self.vertical_select.html('').prop('disabled', true);
                    self.disableFields($('.ccx_due_date_time_fields'));
                    self.enableFields($('.ccx_start_date_time_fields'));
                }
            });

            this.vertical_select.on('change', function() {
                var vertical_location = self.vertical_select.val();
                if (vertical_location !== 'all') {
                    var chapter = self.chapter_select.val(),
                        sequential = self.sequential_select.val();
                    var vertical = self.find_unit(
          self.hidden, chapter, sequential, vertical_location);
          // When a unit (aka vertical) is selected, all date fields are disabled because units
          // inherit dates from subsection
                    self.disableFields($('.ccx_due_date_time_fields'));
                    self.disableFields($('.ccx_start_date_time_fields'));
                } else {
          // When "All units" is selected, all date fields are enabled,
          // because units inherit dates from subsections and we
          // are showing dates from the selected subsection.
                    self.enableFields($('.ccx_due_date_time_fields'));
                    self.enableFields($('.ccx_start_date_time_fields'));
                }
            });

      // Add unit handler
            $('#add-unit-button').on('click', function(event) {
                event.preventDefault();
        // Default value of time is 00:00.
                var start, chapter, sequential, vertical, units, due;
                start = self.get_datetime('start');
                chapter = self.chapter_select.val();
                sequential = self.sequential_select.val();
                vertical = self.vertical_select.val();
                units = self.find_lineage(
          self.schedule,
          chapter,
          sequential === 'all' ? null : sequential,
          vertical === 'all' ? null : vertical
        );
                due = self.get_datetime('due');
                var errorMessage = self.valid_dates(start, due);
                if (_.isUndefined(errorMessage)) {
                    units.map(self.show);
                    var unit = units[units.length - 1];
                    if (!_.isUndefined(unit)) {
                        if (!_.isNull(start)) {
                            unit.start = start;
                        }
                        if (!_.isNull(due)) {
                            unit.due = due;
                        }
                    }
                    self.schedule_apply([unit], self.show);
                    self.schedule_collection.set(self.schedule);
                    self.dirty = true;
                    self.render();
                } else {
                    self.dirty = false;
                    $('#ccx_schedule_error_message').text(errorMessage);
                    $('#ajax-error').show().focus();
                    $('#dirty-schedule').hide();
                }
            });

      // Handle save button
            $('#dirty-schedule #save-changes').on('click', function(event) {
                event.preventDefault();
                self.save();
            });
        }, // end initialization

        render: function() {
            self.schedule = this.schedule_collection.toJSON();
            self.hidden = this.pruned(self.schedule, function(node) {
                return node.hidden || node.category !== 'vertical';
            });
            this.showing = this.pruned(self.schedule, function(node) {
                return !node.hidden;
            });
      // schedule_template defined globally in ccx\schedule.html
      /* globals schedule_template */
            this.$el.html(schedule_template({chapters: this.showing}));
            $('table.ccx-schedule .sequential,.vertical').hide();
            $('table.ccx-schedule .unit .toggle-collapse').on('click', this.toggle_collapse);
      // Hidden hover fields for empty date fields
            $('table.ccx-schedule .date button').each(function() {
                if ($(this).text().trim() === gettext('Click to change')) {
                    $(this).html('Set date <span class="sr"> ' +
          gettext('Click to change') + '</span>');
                }
            });

      // Handle date edit clicks
            $('table.ccx-schedule .date button').attr('href', '#enter-date-modal')
      .leanModal({closeButton: '.close-modal'});
            $('table.ccx-schedule .due-date button').on('click', this.enterNewDate('due'));
            $('table.ccx-schedule .start-date button').on('click', this.enterNewDate('start'));
      // click handler for expand all
            $('#ccx_expand_all_btn').on('click', self.expandAll);
      // click handler for collapse all
            $('#ccx_collapse_all_btn').on('click', self.collapseAll);
      // Click handler for remove all
            $('table.ccx-schedule button#remove-all').on('click', function(event) {
                event.preventDefault();
                self.schedule_apply(self.schedule, self.hide);
                self.dirty = true;
                self.schedule_collection.set(self.schedule);
                self.render();
            });
      // Remove unit handler
            $('table.ccx-schedule button.remove-unit').on('click', function() {
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
        .append('<option value="none">' + gettext('Select a chapter') + '...</option>')
        .append(self.schedule_options(this.hidden));
                this.sequential_select.html('').prop('disabled', true);
                this.vertical_select.html('').prop('disabled', true);
                $('form#add-unit').show();
                $('#all-units-added').hide();
                $('#add-unit-button').prop('disabled', true);
            } else {
                $('form#add-unit').hide();
                $('#all-units-added').show();
            }

      // Show or hide save button
            if (this.dirty) {
                $('#dirty-schedule').show();
                $('html, body').animate(
          {scrollTop: $('#dirty-schedule').offset().top},
          'slow', function() {
              $('#dirty-schedule').focus();
          });
            } else {
                $('#dirty-schedule').hide();
            }
            $('#ajax-error').hide();

            return this;
        }, // end render

        save: function() {
            self.schedule_collection.set(self.schedule);
            var $button = $('#dirty-schedule #save-changes');
            $button.prop('disabled', true).text(gettext('Saving'));
      // save_url defined globally in ccx\schedule.html
      /* globals save_url */
            $.ajax({
                url: save_url,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(self.schedule),
                success: function(data) {
                    self.dirty = false;
                    self.render();
                    $button.prop('disabled', false).text(gettext('Save changes'));

          // Update textarea with grading policy JSON, since grading policy
          // may have changed.
                    $('#grading-policy').text(data.grading_policy);
                },
                error: function(jqXHR) {
                    console.log(jqXHR.responseText);
                    $('#ajax-error').show().focus();
                    $('#dirty-schedule').hide();
                    $('form#add-unit select,input,button').prop('disabled', true);
                    $button.prop('disabled', false).text(gettext('Save changes'));
                }
            });
        }, // end save

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

        valid_dates: function(start, due) {
            var errorMessage;
      // Start date is compulsory and due date is optional.
            if (_.isEmpty(start) && !_.isEmpty(due)) {
                errorMessage = gettext('Please enter valid start date and time.');
            } else if (!_.isEmpty(start) && !_.isEmpty(due)) {
                var requirejs = window.require || RequireJS.require;
                var moment = requirejs('moment');
                var parsedDueDate = moment(due, 'YYYY-MM-DD HH:mm');
                var parsedStartDate = moment(start, 'YYYY-MM-DD HH:mm');
                if (parsedDueDate.isBefore(parsedStartDate)) {
                    errorMessage = gettext('Due date cannot be before start date.');
                }
            }
            return errorMessage;
        },

        get_datetime: function(which) {
            var date = $('form#add-unit input[name=' + which + '_date]').val();
            var time = $('form#add-unit input[name=' + which + '_time]').val();
            time = _.isEmpty(time) ? '00:00' : time;
            if (date && time) {
                return date + ' ' + time;
            }
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
                if (node !== undefined && node.children !== undefined) {
                    self.schedule_apply(node.children, f);
                }
            });
        },

        pruned: function(tree, filter) {
            return tree.filter(filter)
        .map(function(node) {
            var copy = {};
            $.extend(copy, node);
            if (node.children) {
                copy.children = self.pruned(node.children, filter);
            }
            return copy;
        }).filter(function(node) {
            return node.children === undefined || node.children.length;
        });
        },

        disableFields: function($selector) {
            $selector.find('select,input,button').prop('disabled', true);
        },

        enableFields: function($selector) {
            $selector.find('select,input,button').prop('disabled', false);
        },

        toggle_collapse: function(event) {
            event.preventDefault();
            var row = $(this).closest('tr');
            var children = self.get_children(row);

            if (row.is('.expanded')) {
                $(this).attr('aria-expanded', 'false');
                $(this).find('.fa-caret-down').removeClass('fa-caret-down').addClass('fa-caret-right');
                row.removeClass('expanded').addClass('collapsed');
                children.hide();
            } else {
                $(this).attr('aria-expanded', 'true');
                $(this).find('.fa-caret-right').removeClass('fa-caret-right').addClass('fa-caret-down');
                row.removeClass('collapsed').addClass('expanded');
                var depth = $(row).data('depth');
                var $childNodes = children.filter('.collapsed');
                if ($childNodes.length <= 0) {
                    children.show();
                } else {
          // this will expand units.
                    $childNodes.each(function() {
                        var depthChild = $(this).data('depth');
                        if (depth === (depthChild - 1)) {
                            $(this).show();
                        }
                    });
                }
            }
        },

        expandAll: function() {
            $('table.ccx-schedule > tbody > tr').each(function() {
                var $row = $(this);
                if (!$row.is('.expanded')) {
                    var children = self.get_children($row);
                    $row.find('.ccx_sr_alert').attr('aria-expanded', 'true');
                    $row.find('.fa-caret-right').removeClass('fa-caret-right').addClass('fa-caret-down');
                    $row.removeClass('collapsed').addClass('expanded');
                    children.filter('.collapsed').each(function() {
                        children = children.not(self.get_children(this));
                    });
                    children.show();
                }
            });
        },

        collapseAll: function() {
            $('table.ccx-schedule > tbody > tr').each(function() {
                var $row = $(this);
                if ($row.is('.expanded')) {
                    $($row).find('.ccx_sr_alert').attr('aria-expanded', 'false');
                    $($row).find('.fa-caret-down').removeClass('fa-caret-down').addClass('fa-caret-right');
                    $row.removeClass('expanded').addClass('collapsed');
                }
            });
            $('table.ccx-schedule .sequential,.vertical').hide();
        },

        enterNewDate: function(what) {
            return function() {
                var row = $(this).closest('tr');
                var modal = $('#enter-date-modal')
        .data('what', what)
        .data('location', row.data('location'));
                modal.find('h2').text(
          what === 'due' ? gettext('Enter Due Date and Time') :
          gettext('Enter Start Date and Time')
        );
                modal.focus();
                $(document).on('focusin', function(event) {
                    try {
                        if (!_.isUndefined(event.target.closest('.modal').id) &&
              event.target.closest('.modal').id !== 'enter-date-modal' &&
              event.target.id !== 'enter-date-modal') {
                            event.preventDefault();
                            modal.find('.close-modal').focus();
                        }
                    } catch (err) {
                        event.preventDefault();
                        modal.find('.close-modal').focus();
                    }
                });
                modal.find('.close-modal').click(function() {
                    $(document).off('focusin');
                });
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
                        if (unit.category === 'sequential') {
                            self.updateChildrenDates(unit, what, unit.start);
                        }
                    } else {
                        unit.due = date + ' ' + time;
                        if (unit.category === 'sequential') {
                            self.updateChildrenDates(unit, what, unit.due);
                        }
                    }
                    modal.find('.close-modal').click();
                    self.dirty = true;
                    self.schedule_collection.set(self.schedule);
                    self.render();
                });
            };
        },

        updateChildrenDates: function(sequential, date_type, date) {
      // This code iterates the children (aka verticals) of a sequential.
      // It updates start and due dates to corresponding dates
      // of sequential (parent).
            _.forEach(sequential.children, function(unit) {
                if (date_type === 'start') {
                    unit.start = date;
                } else {
                    unit.due = date;
                }
            });
        },

        find_unit: function(tree, chapter, sequential, vertical) {
            var units = self.find_lineage(tree, chapter, sequential, vertical);
            return units[units.length - 1];
        },

        find_lineage: function(tree, chapter, sequential, vertical) {
            function find_in(seq, location) {
                for (var i = 0; i < seq.length; i++) {
                    if (seq[i].location === location) {
                        return seq[i];
                    }
                }
            }
            var units = [],
                unit = find_in(tree, chapter);
            units[units.length] = unit;
            if (sequential) {
                units[units.length] = unit = find_in(unit.children, sequential);
                if (vertical) {
                    units[units.length] = unit = find_in(unit.children, vertical);
                }
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
}(jQuery, _, Backbone, gettext));
