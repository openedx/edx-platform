/**
 * The XBlockOutlineView is used to render an xblock and its children based upon the information
 * provided in the XBlockInfo model. It is a recursive set of views where each XBlock has its own instance.
 *
 * The class provides several opportunities to override the default behavior in subclasses:
 *  - shouldRenderChildren defaults to true meaning that the view should also create child views
 *  - shouldExpandChildren defaults to true meaning that the view should show itself as expanded
 *  - refresh is called when a server change has been made and the view needs to be refreshed
 *
 * The view can be constructed with an initialState option which is a JSON structure representing
 * the desired initial state. The parameters are as follows:
 *  - locator_to_show - the locator for the xblock which is the one being explicitly shown
 *  - scroll_offset - the scroll offset to use for the locator being shown
 *  - edit_display_name - true if the shown xblock's display name should be in inline edit mode
 */
define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/utils/view_utils",
        "js/views/utils/xblock_utils", "js/views/xblock_string_field_editor"],
    function($, _, gettext, BaseView, ViewUtils, XBlockViewUtils, XBlockStringFieldEditor) {

        var XBlockOutlineView = BaseView.extend({
            // takes XBlockInfo as a model

            options: {
                collapsedClass: 'is-collapsed'
            },

            templateName: 'xblock-outline',

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.initialState = this.options.initialState;
                this.expandedLocators = this.options.expandedLocators;
                this.template = this.options.template;
                if (!this.template) {
                    this.template = this.loadTemplate(this.templateName);
                }
                this.parentInfo = this.options.parentInfo;
                this.parentView = this.options.parentView;
                this.renderedChildren = false;
                this.model.on('sync', this.onSync, this);
            },

            render: function() {
                this.renderTemplate();
                this.addButtonActions(this.$el);
                this.addNameEditor();
                if (this.shouldRenderChildren() && this.shouldExpandChildren()) {
                    this.renderChildren();
                }
                else {
                    this.renderedChildren = false;
                }
                return this;
            },

            renderTemplate: function() {
                var xblockInfo = this.model,
                    childInfo = xblockInfo.get('child_info'),
                    parentInfo = this.parentInfo,
                    xblockType = XBlockViewUtils.getXBlockType(this.model.get('category'), this.parentInfo),
                    xblockTypeDisplayName = XBlockViewUtils.getXBlockType(this.model.get('category'), this.parentInfo, true),
                    parentType = parentInfo ? XBlockViewUtils.getXBlockType(parentInfo.get('category')) : null,
                    addChildName = null,
                    defaultNewChildName = null,
                    html,
                    isCollapsed = this.shouldRenderChildren() && !this.shouldExpandChildren();
                if (childInfo) {
                    addChildName = interpolate(gettext('New %(component_type)s'), {
                        component_type: childInfo.display_name
                    }, true);
                    defaultNewChildName = childInfo.display_name;
                }
                html = this.template({
                    xblockInfo: xblockInfo,
                    visibilityClass: XBlockViewUtils.getXBlockVisibilityClass(xblockInfo.get('visibility_state')),
                    typeListClass: XBlockViewUtils.getXBlockListTypeClass(xblockType),
                    parentInfo: this.parentInfo,
                    xblockType: xblockType,
                    xblockTypeDisplayName: xblockTypeDisplayName,
                    parentType: parentType,
                    childType: childInfo ? XBlockViewUtils.getXBlockType(childInfo.category, xblockInfo) : null,
                    childCategory: childInfo ? childInfo.category : null,
                    addChildLabel: addChildName,
                    defaultNewChildName: defaultNewChildName,
                    isCollapsed: isCollapsed,
                    includesChildren: this.shouldRenderChildren(),
                    hasExplicitStaffLock: this.model.get('has_explicit_staff_lock'),
                    staffOnlyMessage: this.model.get('staff_only_message')
                });
                if (this.parentInfo) {
                    this.setElement($(html));
                } else {
                    this.$el.html(html);
                }
            },

            renderChildren: function() {
                var self = this,
                    xblockInfo = this.model;
                if (xblockInfo.get('child_info')) {
                    _.each(this.model.get('child_info').children, function(child) {
                        var childOutlineView = self.createChildView(child, xblockInfo);
                        childOutlineView.render();
                        self.addChildView(childOutlineView);
                    });
                }
                this.renderedChildren = true;
            },

            getListElement: function() {
                return this.$('> .outline-content > ol');
            },

            addChildView: function(childView) {
                this.getListElement().append(childView.$el);
            },

            addNameEditor: function() {
                var self = this,
                    xblockField = this.$('.wrapper-xblock-field'),
                    XBlockOutlineFieldEditor, nameEditor;
                if (xblockField.length > 0) {
                    // Make a subclass of the standard xblock string field editor which refreshes
                    // the entire section that this view is contained in. This is necessary as
                    // changing the name could have caused the section to change state.
                    XBlockOutlineFieldEditor = XBlockStringFieldEditor.extend({
                        refresh: function() {
                            self.refresh();
                        }
                    });
                    nameEditor = new XBlockOutlineFieldEditor({
                        el: xblockField,
                        model: this.model
                    });
                    nameEditor.render();
                }
            },

            toggleExpandCollapse: function(event) {
                // The course outline page tracks expanded locators. The unit location sidebar does not.
                if (this.expandedLocators) {
                    var locator = this.model.get('id');
                    var wasExpanded = this.expandedLocators.contains(locator);
                    if (wasExpanded) {
                        this.expandedLocators.remove(locator);
                    }
                    else {
                        this.expandedLocators.add(locator);
                    }
                }
                // Ensure that the children have been rendered before expanding
                this.ensureChildrenRendered();
                BaseView.prototype.toggleExpandCollapse.call(this, event);
            },

            /**
             * Verifies that the children are rendered (if they should be).
             */
            ensureChildrenRendered: function() {
                if (!this.renderedChildren && this.shouldRenderChildren()) {
                    this.renderChildren();
                }
            },

            /**
             * Adds handlers to the each button in the header's panel. This is managed outside of
             * Backbone's own event registration so that the handlers don't get scoped to all the
             * children of this view.
             * @param element The root element of this view.
             */
            addButtonActions: function(element) {
                var self = this;
                element.find('.delete-button').click(_.bind(this.handleDeleteEvent, this));
                element.find('.button-new').click(_.bind(this.handleAddEvent, this));
            },

            shouldRenderChildren: function() {
                return true;
            },

            shouldExpandChildren: function() {
                return true;
            },

            createChildView: function(xblockInfo, parentInfo, parentView) {
                return new XBlockOutlineView({
                    model: xblockInfo,
                    parentInfo: parentInfo,
                    initialState: this.initialState,
                    expandedLocators: this.expandedLocators,
                    template: this.template,
                    parentView: parentView || this
                });
            },

            onSync: function(event) {
                if (ViewUtils.hasChangedAttributes(this.model, ['visibility_state', 'child_info', 'display_name'])) {
                   this.onXBlockChange();
                }
            },

            onXBlockChange: function() {
                var oldElement = this.$el,
                    viewState = this.initialState;
                this.render();
                if (this.parentInfo) {
                    oldElement.replaceWith(this.$el);
                }
                if (viewState) {
                    this.setViewState(viewState);
                }
            },

            setViewState: function(viewState) {
                var locatorToShow = viewState.locator_to_show,
                    scrollOffset = viewState.scroll_offset || 0,
                    editDisplayName = viewState.edit_display_name,
                    locatorElement;
                if (locatorToShow) {
                    if (locatorToShow === this.model.id) {
                        locatorElement = this.$el;
                    } else {
                        locatorElement = this.$('.outline-item[data-locator="' + locatorToShow + '"]');
                    }
                    if (locatorElement.length > 0) {
                        ViewUtils.setScrollOffset(locatorElement, scrollOffset);
                    } else {
                        console.error("Failed to show item with locator " + locatorToShow + "");
                    }
                    if (editDisplayName) {
                        locatorElement.find('> div[class$="header"] .xblock-field-value-edit').click();
                    }
                }
                this.initialState = null;
            },

            /**
             * Refresh the view's model from the server, which will cause the view to refresh.
             * @returns {jQuery promise} A promise representing the refresh operation.
             */
            refresh: function() {
                return this.model.fetch();
            },

            onChildAdded: function(locator, category) {
                // For units, redirect to the new page, and for everything else just refresh inline.
                if (category === 'vertical') {
                    this.onUnitAdded(locator);
                } else {
                    this.refresh();
                }
            },

            onUnitAdded: function(locator) {
                ViewUtils.redirect('/container/' + locator + '?action=new');
            },

            onChildDeleted: function() {
                this.refresh();
            },

            handleDeleteEvent: function(event) {
                var self = this,
                    parentView = this.parentView;
                event.preventDefault();
                var xblockType = XBlockViewUtils.getXBlockType(this.model.get('category'), parentView.model, true);
                XBlockViewUtils.deleteXBlock(this.model, xblockType).done(function() {
                    if (parentView) {
                        parentView.onChildDeleted(self, event);
                    }
                });
            },

            handleAddEvent: function(event) {
                var self = this,
                    target = $(event.target),
                    category = target.data('category');
                event.preventDefault();
                XBlockViewUtils.addXBlock(target).done(function(locator) {
                    self.onChildAdded(locator, category, event);
                });
            }
        });

        return XBlockOutlineView;
    }); // end define();
