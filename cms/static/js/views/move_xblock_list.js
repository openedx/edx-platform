/**
 * XBlockListView shows list of XBlocks in a particular category(section, subsection, vertical etc).
 */
define([
    'jquery', 'backbone', 'underscore', 'gettext',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'js/views/utils/xblock_utils',
    'text!templates/move-xblock-list.underscore'
],
function($, Backbone, _, gettext, HtmlUtils, StringUtils, XBlockUtils, MoveXBlockListViewTemplate) {
    'use strict';

    var XBlockListView = Backbone.View.extend({
        // parent info of currently displayed childs
        parent_info: {},
        // child info of currently displayed child XBlocks
        childs_info: {},
        // list of visited parent XBlocks, needed for backward navigation
        visitedAncestors: null,

        // parent to child relation map
        categoryRelationMap: {
            course: 'section',
            section: 'subsection',
            subsection: 'unit',
            unit: 'component'
        },

        categoriesText: {
            section: gettext('Sections'),
            subsection: gettext('Subsections'),
            unit: gettext('Units'),
            component: gettext('Components')
        },

        events: {
            'click .button-forward': 'renderChilds'
        },

        initialize: function() {
            this.visitedAncestors = [];
            this.template = HtmlUtils.template(MoveXBlockListViewTemplate);
            this.listenTo(Backbone, 'move:backButtonPressed', this.handleBackButtonPress);
            this.listenTo(Backbone, 'move:breadcrumbButtonPressed', this.handleBreadcrumbButtonPress);
            this.renderXBlockInfo();
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                this.template(
                    {
                        xblocks: this.childs_info.childs,
                        noChildText: this.getNoChildText(),
                        categoryText: this.getCategoryText(),
                        showForwardButton: this.showForwardButton(),
                        forwardButtonSRText: this.getForwardButtonSRText()
                    }
                )
            );
            Backbone.trigger('move:childsInfoRendered', this.breadcrumbInfo());
            return this;
        },

        renderChilds: function(event) {
            this.renderXBlockInfo(
                'forward',
                $(event.target).closest('.xblock-item').data('itemIndex')
            );
        },

        renderParent: function(newParentIndex) {
            this.renderXBlockInfo('backward', newParentIndex);
        },

        handleBackButtonPress: function() {
            // TODO! improve `this.visitedAncestors.length - 2` mysterious calculation
            this.renderParent(this.visitedAncestors.length - 2);
        },

        handleBreadcrumbButtonPress: function(newParentIndex) {
            this.renderParent(newParentIndex);
        },

        renderXBlockInfo: function(direction, newParentIndex) {
            if (direction === undefined) {
                this.parent_info.parent = this.model;
            } else if (direction === 'forward') {
                // clicked child is the new parent
                this.parent_info.parent = this.childs_info.childs[newParentIndex];
            } else if (direction === 'backward') {
                // new parent will be one of visitedAncestors
                this.parent_info.parent = this.visitedAncestors[newParentIndex];
                // remove visited ancestors
                this.visitedAncestors.splice(newParentIndex);
            }

            this.visitedAncestors.push(this.parent_info.parent);

            if (this.parent_info.parent.get('child_info')) {
                this.childs_info.childs = this.parent_info.parent.get('child_info').children;
            } else {
                this.childs_info.childs = [];
            }

            this.validateMoveOperation();
            this.setDisplayedXBlocksCategories();
            this.render();
        },

        validateMoveOperation: function() {
            Backbone.trigger('move:validateMoveOperation', this.parent_info.parent);
        },

        setDisplayedXBlocksCategories: function() {
            this.parent_info.category = XBlockUtils.getXBlockType(
                this.parent_info.parent.get('category'),
                // TODO! improve `this.visitedAncestors.length - 2` mysterious calculation
                this.visitedAncestors[this.visitedAncestors.length - 2]
            );
            this.childs_info.category = this.categoryRelationMap[this.parent_info.category];
        },

        getCategoryText: function() {
            return this.categoriesText[this.childs_info.category];
        },

        getForwardButtonSRText: function() {
            return StringUtils.interpolate(
                gettext('Press button to see {XBlockCategory} childs'),
                {XBlockCategory: this.childs_info.category}
            );
        },

        getNoChildText: function() {
            return StringUtils.interpolate(
                gettext('This {parentCategory} has no {childCategory}'),
                {
                    parentCategory: this.parent_info.category,
                    childCategory: this.categoriesText[this.childs_info.category].toLowerCase()
                }
            );
        },

        breadcrumbInfo: function() {
            return {
                backButtonEnabled: this.parent_info.category !== 'course',
                breadcrumbs: _.map(this.visitedAncestors, function(ancestor) {
                    return ancestor.get('category') === 'course' ?
                           gettext('Course Outline') : ancestor.get('display_name');
                })
            };
        },

        showForwardButton: function() {
            return this.childs_info.category !== 'component';
        }
    });

    return XBlockListView;
});
