(function(define) {
    'use strict';
    define([
        'backbone',
        'jquery',
        'underscore',
        'js/ccx/view/schedule_tree',
        'js/ccx/view/schedule_right_container',
        'text!templates/ccx/underscore/schedule.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(Backbone,
        $,
        _,
        ScheduleTree,
        ScheduleRightContainerView,
        scheduleTemplate,
        HtmlUtils) {
        return Backbone.View.extend({

            initialize: function(options) {
                var self = this;
                this.template = HtmlUtils.template(scheduleTemplate);
                this.saveCCXScheduleUrl = options.saveCCXScheduleUrl;
                this.unsavedChanges = false;
                this.collection.bind('change add remove reset', function() {
                    self.unsavedChanges = true;
                    self.render();
                });
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template()
                );
                this.loadScheduleTree();
                this.loadScheduleRightContainer();
                return this;
            },

            loadScheduleRightContainer: function() {
                // Right container consist of a form and alert messages.
                this.scheduleRightContainer = new ScheduleRightContainerView({
                    el: this.$('#ccx-schedule-form'),
                    collection: this.collection,
                    unsavedChanges: this.unsavedChanges
                });

                this.scheduleRightContainer.render();
                this.$('#ajax-error').hide();
                this.listenTo(
                    this.scheduleRightContainer,
                    'showUnitInScheduleTree',
                    this.showUnitInScheduleTree
                );
                this.listenTo(
                    this.scheduleRightContainer,
                    'showAllUnitsInScheduleTree',
                    this.showAllUnitsInScheduleTree
                );
                this.listenTo(
                    this.scheduleRightContainer,
                    'saveSchedule',
                    this.saveSchedule
                );
            },

            loadScheduleTree: function() {
                // This data will be render on schedule tree.
                this.scheduleTreeView = new ScheduleTree({
                    el: this.$('#new-ccx-schedule'),
                    collection: this.collection
                });

                this.scheduleTreeView.render();
                this.listenTo(
                    this.scheduleTreeView,
                    'hideAllUnitFromScheduleTree',
                    this.hideAllUnitFromScheduleTree
                );
                this.listenTo(
                    this.scheduleTreeView,
                    'hideUnitFromScheduleTree',
                    this.hideUnitFromScheduleTree
                );
                this.listenTo(
                    this.scheduleTreeView,
                    'applyUnitToScheduleTree',
                    this.applyUnitToScheduleTree
                );
            },

            saveSchedule: function() {
                // saves schedule on server.
                var self = this;
                Backbone.ajax({
                    url: this.saveCCXScheduleUrl,
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(this.collection),
                    success: function(data) {
                        self.unsavedChanges = false;
                        self.render();
                        $('#grading-policy').text(HtmlUtils.ensureHtml(data.grading_policy));
                    },
                    error: function() {
                        self.showErrorMessage();
                        self.scheduleRightContainer.resetSaveChangesButton();
                    }
                });
            },

            applyUnitToScheduleTree: function(dateType,
                                               newDate,
                                               chapterLocation,
                                               sequentialLocation,
                                               verticalLocation) {
                // updates collection on start, due date change in chapter or sequential
                this.errorMessage = this.collection.applyUnitToScheduleTree(
                    dateType,
                    newDate,
                    chapterLocation,
                    sequentialLocation,
                    verticalLocation
                );
                if (this.errorMessage) {
                    this.showErrorMessage();
                }
            },

            hideUnitFromScheduleTree: function(chapterLocation, sequentialLocation,
                                                verticalLocation) {
                // hide child (can be chapter, sequential or vertical) in collection.
                this.collection.hideUnitFromScheduleTree(
                    chapterLocation,
                    sequentialLocation,
                    verticalLocation
                );
            },

            hideAllUnitFromScheduleTree: function() {
                // clear schedule tree on remove all click
                this.collection.hideAllUnitFromScheduleTree();
            },

            showUnitInScheduleTree: function(chapterLocation, sequentialLocation, verticalLocation,
                                              startDate, dueDate) {
                // hide child (can be chapter, sequential or vertical) in collection.
                this.errorMessage = this.collection.showUnitInScheduleTree(
                    chapterLocation,
                    sequentialLocation,
                    verticalLocation,
                    startDate,
                    dueDate
                );

                if (this.errorMessage) {
                    this.showErrorMessage();
                }
            },

            showAllUnitsInScheduleTree: function() {
                // show all units i.e chapters, subsections and verticals
                // in schedule tree
                this.collection.showAllUnitsInScheduleTree();
            },

            showErrorMessage: function() {
                if (this.errorMessage) {
                    HtmlUtils.setHtml(
                        this.$('#ccx_schedule_error_message'),
                        HtmlUtils.ensureHtml(this.errorMessage)
                    );
                }
                this.$('#ajax-error').show().focus();
            }
        });
    });
}).call(this, define || RequireJS.define);
