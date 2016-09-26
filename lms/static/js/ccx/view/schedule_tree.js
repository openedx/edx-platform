/* eslint dollar-sign/dollar-sign: "off" */
(function(define) {
    'use strict';
    define([
        'backbone',
        'jquery',
        'underscore',
        'js/ccx/view/schedule_date_button',
        'text!templates/ccx/underscore/unit.underscore',
        'text!templates/ccx/underscore/tree.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(
        Backbone,
        $,
        _,
        DateButtonView,
        scheduleTreeNodeTemplate,
        scheduleTreeContentTemplate,
        HtmlUtils) {
        return Backbone.View.extend({

            events: {
                'click .remove-unit': 'removeUnitFromTree',
                'click #remove-all': 'removeAllUnitFromTree',
                'click .toggle-collapse': 'toggleNodeState',
                'click #ccx_expand_all_btn': 'expandAll',
                'click #ccx_collapse_all_btn': 'collapseAll'
            },

            initialize: function() {
                this.templateTreeNode = HtmlUtils.template(scheduleTreeNodeTemplate);
                this.templateTree = HtmlUtils.template(scheduleTreeContentTemplate);
            },

            render: function() {
                this.chapters = this.collection.filterTreeData();
                if (this.chapters) {
                    HtmlUtils.setHtml(
                        this.$el,
                        this.templateTree({
                            chapters: this.chapters,
                            templateTreeNode: this.templateTreeNode
                        })
                    );
                    this.configureEditDateViews();
                }
                return this;
            },

            configureEditDateViews: function() {
                var self = this;
                this.$('table.ccx-schedule .due-date').each(function() {
                    var date = $(this).data('date');
                    var scheduleDateButtonView = new DateButtonView({
                        el: $(this),
                        date: date,
                        dateType: 'due'
                    });
                    scheduleDateButtonView.render();
                    self.listenTo(
                        scheduleDateButtonView,
                        'updateDate',
                        self.updateDate
                    );
                });

                this.$el.find('table.ccx-schedule .start-date').each(function() {
                    var date = $(this).data('date');
                    var scheduleDateButtonView = new DateButtonView({
                        el: $(this),
                        date: date,
                        dateType: 'start'
                    });
                    scheduleDateButtonView.render();
                    self.listenTo(
                        scheduleDateButtonView,
                        'updateDate',
                        self.updateDate
                    );
                });
            },

            updateDate: function(dateType, newDate, location) {
                var path = location.split(' ');
                var chapterLocation = path[0];
                var sequentialLocation = path[1];
                var verticalLocation = path[2];

                this.trigger(
                    'applyUnitToScheduleTree',
                    dateType,
                    newDate,
                    chapterLocation,
                    sequentialLocation,
                    verticalLocation
                );
            },

            removeUnitFromTree: function(e) {
                // remove a unit which can be chapter, sequential
                // or vertical from schedule tree
                var target = e.target || e.srcElement;
                var location = $(target).data('location');
                var path = location.split(' ');
                var chapterLocation = path[0];
                var sequentialLocation = path[1];
                var verticalLocation = path[2];
                e.preventDefault();

                this.trigger(
                    'hideUnitFromScheduleTree',
                    chapterLocation,
                    sequentialLocation,
                    verticalLocation
                );
            },

            removeAllUnitFromTree: function() {
                this.trigger('hideAllUnitFromScheduleTree');
            },

            toggleNodeState: function(e) {
                // expand or collapse node (chapter or sequential)
                var target = e.target || e.srcElement;
                var row = $(target).closest('tr');
                var children = this.getChildrenInView(row);
                var depth;
                var $childNodes;

                e.preventDefault();
                if (row.is('.expanded')) {
                    $(target).attr('aria-expanded', 'false');
                    $(target).find('.fa-caret-down').removeClass('fa-caret-down')
                        .addClass('fa-caret-right');
                    row.removeClass('expanded').addClass('collapsed');
                    children.hide();
                } else {
                    $(target).attr('aria-expanded', 'true');
                    $(target).find('.fa-caret-right').removeClass('fa-caret-right')
                        .addClass('fa-caret-down');
                    row.removeClass('collapsed').addClass('expanded');
                    depth = $(row).data('depth');
                    $childNodes = children.filter('.collapsed');
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

            getChildrenInView: function(row) {
                var depth = $(row).data('depth');
                return $(row).nextUntil(
                    $(row).siblings().filter(function() {
                        return $(this).data('depth') <= depth;
                    })
                );
            },

            expandAll: function() {
                var self = this;
                this.$('table.ccx-schedule > tbody > tr').each(function() {
                    var row = $(this);
                    var children;

                    if (!row.is('.expanded')) {
                        children = self.getChildrenInView(row);
                        row.find('.ccx_sr_alert').attr('aria-expanded', 'true');
                        row.find('.fa-caret-right').removeClass(
                            'fa-caret-right'
                        ).addClass('fa-caret-down');
                        row.removeClass('collapsed').addClass('expanded');
                        children.filter('.collapsed').each(function() {
                            children = children.not(self.getChildrenInView(this));
                        });
                        children.show();
                    }
                });
            },

            collapseAll: function() {
                this.$('table.ccx-schedule > tbody > tr').each(function() {
                    var row = $(this);
                    if (row.is('.expanded')) {
                        $(row).find('.ccx_sr_alert').attr('aria-expanded', 'false');
                        $(row).find('.fa-caret-down')
                            .removeClass('fa-caret-down')
                            .addClass('fa-caret-right');
                        row.removeClass('expanded').addClass('collapsed');
                    }
                });
                this.$el.find('table.ccx-schedule .sequential,.vertical').hide();
            }
        });
    });
}).call(this, define || RequireJS.define);
