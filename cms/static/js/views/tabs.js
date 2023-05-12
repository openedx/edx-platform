/* globals analytics, course_location_analytics */

// eslint-disable-next-line camelcase
(function(analytics, course_location_analytics) {
    'use strict';

    // eslint-disable-next-line no-var
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            // eslint-disable-next-line no-var
            var key;
            // eslint-disable-next-line no-restricted-syntax
            for (key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function Ctor() {
                this.constructor = child;
            }
            Ctor.prototype = parent.prototype;
            child.prototype = new Ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    // eslint-disable-next-line no-undef
    define(['underscore', 'jquery', 'jquery.ui', 'backbone', 'common/js/components/views/feedback_prompt',
        'common/js/components/views/feedback_notification', 'js/views/module_edit',
        'js/models/module_info', 'js/utils/module'],
    function(_, $, ui, Backbone, PromptView, NotificationView, ModuleEditView, ModuleModel, ModuleUtils) {
        // eslint-disable-next-line no-var
        var TabsEdit;
        TabsEdit = (function(_super) {
            // eslint-disable-next-line no-use-before-define
            __extends(TabsEdit, _super);

            // eslint-disable-next-line no-shadow
            function TabsEdit() {
                // eslint-disable-next-line no-var
                var self = this;
                this.deleteTab = function() {
                    return TabsEdit.prototype.deleteTab.apply(self, arguments);
                };
                this.addNewTab = function() {
                    return TabsEdit.prototype.addNewTab.apply(self, arguments);
                };
                this.tabMoved = function() {
                    return TabsEdit.prototype.tabMoved.apply(self, arguments);
                };
                this.toggleVisibilityOfTab = function() {
                    return TabsEdit.prototype.toggleVisibilityOfTab.apply(self, arguments);
                };
                this.initialize = function() {
                    return TabsEdit.prototype.initialize.apply(self, arguments);
                };
                return TabsEdit.__super__.constructor.apply(this, arguments);
            }

            TabsEdit.prototype.initialize = function(options) {
                // eslint-disable-next-line no-var
                var self = this;
                this.$('.component').each(function(idx, element) {
                    // eslint-disable-next-line no-var
                    var model;
                    model = new ModuleModel({
                        id: $(element).data('locator')
                    });
                    return new ModuleEditView({
                        el: element,
                        onDelete: self.deleteTab,
                        model: model
                    });
                });
                this.options = _.extend({}, options);
                this.options.mast.find('.new-tab').on('click', this.addNewTab);
                $('.add-pages .new-tab').on('click', this.addNewTab);
                $('.toggle-checkbox').on('click', this.toggleVisibilityOfTab);
                return this.$('.course-nav-list').sortable({
                    handle: '.drag-handle',
                    update: this.tabMoved,
                    helper: 'clone',
                    opacity: '0.5',
                    placeholder: 'component-placeholder',
                    forcePlaceholderSize: true,
                    axis: 'y',
                    items: '> .is-movable'
                });
            };

            TabsEdit.prototype.toggleVisibilityOfTab = function(event) {
                /* eslint-disable-next-line camelcase, no-var */
                var checkbox_element, saving, tab_element;
                // eslint-disable-next-line camelcase
                checkbox_element = event.target;
                // eslint-disable-next-line camelcase
                tab_element = $(checkbox_element).parents('.course-tab')[0];
                saving = new NotificationView.Mini({
                    title: gettext('Saving')
                });
                saving.show();
                return $.ajax({
                    type: 'POST',
                    url: this.model.url(),
                    data: JSON.stringify({
                        tab_id_locator: {
                            tab_id: $(tab_element).data('tab-id'),
                            tab_locator: $(tab_element).data('locator')
                        },
                        is_hidden: $(checkbox_element).is(':checked')
                    }),
                    contentType: 'application/json'
                }).success(function() {
                    return saving.hide();
                });
            };

            TabsEdit.prototype.tabMoved = function() {
                // eslint-disable-next-line no-var
                var saving, tabs;
                tabs = [];
                this.$('.course-tab').each(function(idx, element) {
                    return tabs.push({
                        tab_id: $(element).data('tab-id'),
                        tab_locator: $(element).data('locator')
                    });
                });
                analytics.track('Reordered Pages', {
                    // eslint-disable-next-line camelcase
                    course: course_location_analytics
                });
                saving = new NotificationView.Mini({
                    title: gettext('Saving')
                });
                saving.show();
                return $.ajax({
                    type: 'POST',
                    url: this.model.url(),
                    data: JSON.stringify({
                        tabs: tabs
                    }),
                    contentType: 'application/json'
                }).success(function() {
                    return saving.hide();
                });
            };

            TabsEdit.prototype.addNewTab = function(event) {
                // eslint-disable-next-line no-var
                var editor;
                event.preventDefault();
                editor = new ModuleEditView({
                    onDelete: this.deleteTab,
                    model: new ModuleModel()
                });
                $('.new-component-item').before(editor.$el);
                editor.$el.addClass('course-tab is-movable');
                editor.$el.addClass('new');
                setTimeout(function() {
                    return editor.$el.removeClass('new');
                }, 1000);
                $('html, body').animate({
                    scrollTop: $('.new-component-item').offset().top
                }, 500);
                editor.createItem(this.model.get('id'), {
                    category: 'static_tab'
                });
                return analytics.track('Added Page', {
                    // eslint-disable-next-line camelcase
                    course: course_location_analytics
                });
            };

            TabsEdit.prototype.deleteTab = function(event) {
                // eslint-disable-next-line no-var
                var confirm;
                confirm = new PromptView.Warning({
                    title: gettext('Delete Page Confirmation'),
                    message: gettext('Are you sure you want to delete this page? This action cannot be undone.'),
                    actions: {
                        primary: {
                            text: gettext('OK'),
                            click: function(view) {
                                // eslint-disable-next-line no-var
                                var $component, deleting;
                                view.hide();
                                $component = $(event.currentTarget).parents('.component');
                                analytics.track('Deleted Page', {
                                    // eslint-disable-next-line camelcase
                                    course: course_location_analytics,
                                    id: $component.data('locator')
                                });
                                deleting = new NotificationView.Mini({
                                    title: gettext('Deleting')
                                });
                                deleting.show();
                                return $.ajax({
                                    type: 'DELETE',
                                    url: ModuleUtils.getUpdateUrl($component.data('locator'))
                                }).success(function() {
                                    $component.remove();
                                    return deleting.hide();
                                });
                            }
                        },
                        secondary: [
                            {
                                text: gettext('Cancel'),
                                click: function(view) {
                                    return view.hide();
                                }
                            }
                        ]
                    }
                });
                return confirm.show();
            };

            return TabsEdit;
        }(Backbone.View));
        return TabsEdit;
    });
}).call(this, analytics, course_location_analytics);
