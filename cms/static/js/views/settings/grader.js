define(['js/views/validation',
    'gettext',
    'edx-ui-toolkit/js/utils/string-utils',
    'edx-ui-toolkit/js/utils/html-utils',
    'underscore',
    'jquery'],
    function(ValidatingView, gettext, StringUtils, HtmlUtils, _, $) {
        var GraderView = ValidatingView.extend({
    // Model class is CMS.Models.Settings.CourseGrader
            events: {
                'input input': 'updateModel',
                'input textarea': 'updateModel',
        // Leaving change in as fallback for older browsers
                'change input': 'updateModel',
                'change textarea': 'updateModel',
                'click .remove-grading-data': 'deleteModel',
        // would love to move to a general superclass, but event hashes don't inherit in backbone :-(
                'focus :input': 'inputFocus',
                'blur :input': 'inputUnfocus'
            },
            initialize: function() {
                this.listenTo(this.model, 'invalid', this.handleValidationError);
                this.selectorToField = _.invert(this.fieldToSelectorMap);
                this.render();
            },

            render: function() {
                return this;
            },
            fieldToSelectorMap: {
                type: 'course-grading-assignment-name',
                short_label: 'course-grading-assignment-shortname',
                min_count: 'course-grading-assignment-totalassignments',
                drop_count: 'course-grading-assignment-droppable',
                weight: 'course-grading-assignment-gradeweight'
            },
            updateModel: function(event) {
        // HACK to fix model sometimes losing its pointer to the collection [I think I fixed this but leaving
        // this in out of paranoia. If this error ever happens, the user will get a warning that they cannot
        // give 2 assignments the same name.]
                if (!this.model.collection) {
                    this.model.collection = this.collection;
                }

                switch (event.currentTarget.id) {
                case 'course-grading-assignment-totalassignments':
                    this.$el.find('#course-grading-assignment-droppable').attr('max', $(event.currentTarget).val());
                    this.setField(event);
                    break;
                case 'course-grading-assignment-name':
            // Keep the original name, until we save
                    this.oldName = this.oldName === undefined ? this.model.get('type') : this.oldName;
            // If the name has changed, alert the user to change all subsection names.
                    if (this.setField(event) != this.oldName && !_.isEmpty(this.oldName)) {
                // overload the error display logic
                        this._cacheValidationErrors.push(event.currentTarget);
                        var message = StringUtils.interpolate(
                    gettext('For grading to work, you must change all {oldName} subsections to {newName}.'),
                            {
                                oldName: this.oldName,
                                newName: this.model.get('type')
                            }
                );
                        HtmlUtils.append($(event.currentTarget).parent(), this.errorTemplate({message: message}));
                    }
                    break;
                default:
                    this.setField(event);
                    break;
                }
            },
            deleteModel: function(e) {
                e.preventDefault();
                this.collection.remove(this.model);
            }
        });

        return GraderView;
    }); // end define()
