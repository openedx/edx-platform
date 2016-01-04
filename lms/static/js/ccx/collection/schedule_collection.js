;(function (define) {
    'use strict';
    define([
            'backbone',
            'underscore',
            'gettext',
            'moment',
            'js/ccx/model/schedule_model',
            'edx-ui-toolkit/js/utils/string-utils'
        ],
        function (Backbone, _, gettext, moment, ccxScheduleModel, StringUtils) {
            return Backbone.Collection.extend({
                model: ccxScheduleModel,
                url: 'ccx_schedule',

                showAllUnitsInScheduleTree: function () {
                    // show all units i.e chapters, subsections and verticals
                    // in schedule tree
                    var scheduleJson = this.toJSON();
                    this.changeVisibilityOfUnitInSchedule(
                        scheduleJson, this.show
                    );
                    this.reset(scheduleJson);
                },

                hideAllUnitFromScheduleTree: function () {
                    // clear schedule tree on remove all click
                    var scheduleJson = this.toJSON();
                    this.changeVisibilityOfUnitInSchedule(
                        scheduleJson, this.hide
                    );
                    this.reset(scheduleJson);
                },

                hideUnitFromScheduleTree: function (chapterLocation, sequentialLocation,
                                                    verticalLocation) {
                    // hide child (can be chapter, sequential or vertical) in collection.
                    var scheduleJson = this.toJSON();
                    var unit = this.findUnit(
                        scheduleJson,
                        chapterLocation,
                        sequentialLocation,
                        verticalLocation
                    );

                    if (unit) {
                        this.changeVisibilityOfUnitInSchedule(
                            [unit],
                            this.hide
                        );
                        this.reset(scheduleJson);
                    }
                },

                filterTreeData: function () {
                    return this.pruned(this.toJSON(), this.treeFilter);
                },

                filterFormData: function () {
                    return this.pruned(this.toJSON(), this.formFilter);
                },

                showUnitInScheduleTree: function (chapterLocation,
                                                  sequentialLocation,
                                                  verticalLocation,
                                                  startDate,
                                                  dueDate) {
                    // hide child (can be chapter, sequential or vertical) in collection.
                    var scheduleJson = this.toJSON();
                    var errorMessage;

                    var units = this.findLineage(
                        scheduleJson,
                        chapterLocation,
                        sequentialLocation,
                        verticalLocation
                    );

                    if (units) {
                        errorMessage = this.validUnitDates(startDate, dueDate, units[units.length - 1]);
                        if (!errorMessage) {
                            units.map(this.show);
                            var unit = units[units.length - 1];
                            if (!_.isUndefined(unit)) {
                                unit.start = startDate;
                                unit.due = dueDate;
                                if (unit.category === 'sequential' && unit.children) {
                                    _.each(unit.children, function (vertical) {
                                        vertical.start = startDate;
                                        vertical.due = dueDate;
                                    });
                                }
                            }
                            this.changeVisibilityOfUnitInSchedule([unit], this.show);
                            this.reset(scheduleJson);
                        }
                    }
                    return errorMessage;
                },

                applyUnitToScheduleTree: function (dateType,
                                                   newDate,
                                                   chapterLocation,
                                                   sequentialLocation,
                                                   verticalLocation) {
                    // updates collection on start, due date change in chapter or sequential
                    var scheduleJson = this.toJSON();
                    var errorMessage;

                    var unit = this.findUnit(
                        scheduleJson,
                        chapterLocation,
                        sequentialLocation,
                        verticalLocation
                    );

                    if (unit) {
                        if (dateType === 'start') {
                            unit.start = newDate;
                        } else {
                            unit.due = newDate;
                        }
                        this.applyUnitToTree(
                            scheduleJson,
                            unit,
                            chapterLocation,
                            sequentialLocation
                        );
                        errorMessage = this.validUnitDates(unit.start, unit.due, unit);
                        if (!errorMessage) {
                            this.reset(scheduleJson);
                        }
                    }
                    return errorMessage;
                },

                applyUnitToTree: function (tree, unit, chapterLocation, sequentialLocation) {
                    // sync tree ith unit
                    if (!chapterLocation) {
                        return;
                    }
                    _.each(tree, function (chapter, chapterIndex) {
                        if (chapter.location === chapterLocation) {
                            if (chapter.location === unit.location) {
                                tree[chapterIndex] = unit;
                                return true;
                            }
                            _.each(chapter.children, function (subSection, subSectionIndex) {
                                if (subSection.location === sequentialLocation &&
                                    subSection.location === unit.location) {
                                    // update that subsection in tree
                                    tree[chapterIndex].children[subSectionIndex] = unit;

                                    _.each(subSection.children, function (__, verticalIndex) {
                                        // update start and due dates of verticals
                                        tree[chapterIndex].children[subSectionIndex].
                                            children[verticalIndex].start = unit.start;

                                        tree[chapterIndex].children[subSectionIndex].
                                            children[verticalIndex].due = unit.due;
                                    });
                                    return true;
                                }
                            });
                            return true;
                        }
                    });
                },

                pruned: function (tree, filter) {
                    var self = this;
                    return tree.filter(filter)
                        .map(function (node) {
                            var copy = {};
                            $.extend(copy, node);
                            if (node.children) {
                                copy.children = self.pruned(node.children, filter);
                            }
                            return copy;
                        }).filter(function (node) {
                            return node.children === undefined || node.children.length;
                        });
                },

                treeFilter: function (unit) {
                    return !unit.hidden;
                },

                formFilter: function (unit) {
                    return unit.hidden || unit.category !== 'vertical';
                },

                changeVisibilityOfUnitInSchedule: function (units, applyVisibility) {
                    var self = this;
                    units.map(function (unit) {
                        applyVisibility(unit);
                        if (unit !== undefined && unit.children !== undefined) {
                            self.changeVisibilityOfUnitInSchedule(unit.children, applyVisibility);
                        }
                    });
                },

                hide: function (unit) {
                    if (unit !== undefined) {
                        unit.hidden = true;
                    }
                },

                show: function (unit) {
                    if (unit !== undefined) {
                        unit.hidden = false;
                    }
                },

                validUnitDates: function (start, due, unit) {
                    var errorMessage;
                    // Start date is compulsory and due date is optional.
                    if (_.isEmpty(start) && !_.isEmpty(due)) {
                        errorMessage = StringUtils.interpolate(
                            gettext(
                                'Please enter valid start ' +
                                'date and time for {type} "{displayName}".'
                            ),
                            { 'displayName': unit.display_name, 'type': unit.category }
                        );
                    } else if (!_.isEmpty(start) && !_.isEmpty(due)) {
                        var parsedDueDate = moment(due, 'YYYY-MM-DD HH:mm');
                        var parsedStartDate = moment(start, 'YYYY-MM-DD HH:mm');
                        if (parsedDueDate.isBefore(parsedStartDate)) {
                            errorMessage = StringUtils.interpolate(
                                gettext(
                                    'Due date cannot be before ' +
                                    'start date for {type} "{displayName}"'
                                ),
                                {'displayName': unit.display_name, 'type': unit.category}
                            );
                        }
                    }
                    return errorMessage;
                },

                findLineage: function (tree, chapterLocation, sequentialLocation, verticalLocation) {
                    var units = [];
                    var chapter = this.findUnitAtLocation(tree, chapterLocation);
                    units[units.length] = chapter;
                    if (sequentialLocation) {
                        var sequential = this.findUnitAtLocation(
                            chapter.children, sequentialLocation
                        );
                        units[units.length] = sequential;
                        if (verticalLocation) {
                            units[units.length] = this.findUnitAtLocation(
                                sequential.children, verticalLocation
                            );
                        }
                    }
                    return units;
                },

                findUnit: function (tree, chapter, sequential, vertical) {
                    var units = this.findLineage(tree, chapter, sequential, vertical);
                    return units[units.length - 1];
                },

                findUnitAtLocation: function (seq, location) {
                    for (var i = 0; i < seq.length; i++) {
                        if (seq[i].location === location) {
                            return seq[i];
                        }
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);