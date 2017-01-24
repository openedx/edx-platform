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
        el: '.xblock-list-container',

        // parent info of currently displayed children
        parentInfo: {},
        // currently displayed children XBlocks info
        childrenInfo: {},
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
            'click .button-forward': 'renderChildren'
        },

        initialize: function(options) {
            this.visitedAncestors = [];
            this.template = HtmlUtils.template(MoveXBlockListViewTemplate);
            this.ancestorInfo = options.ancestorInfo;
            this.listenTo(Backbone, 'move:breadcrumbButtonPressed', this.handleBreadcrumbButtonPress);
            this.renderXBlockInfo();
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                this.template(
                    {
                        xblocks: this.childrenInfo.children,
                        noChildText: this.getNoChildText(),
                        categoryText: this.getCategoryText(),
                        parentDisplayname: this.parentInfo.parent.get('display_name'),
                        XBlocksCategory: this.childrenInfo.category,
                        currentLocationIndex: this.getCurrentLocationIndex()
                    }
                )
            );
            Backbone.trigger('move:childrenRendered', this.breadcrumbInfo());
            Backbone.trigger('move:enableMoveOperation', this.parentInfo.parent);
            return this;
        },

        /**
         * Forward button press handler. This will render all the childs of an XBlock.
         *
         * @param {Object} event
         */
        renderChildren: function(event) {
            this.renderXBlockInfo(
                'forward',
                $(event.target).closest('.xblock-item').data('itemIndex')
            );
        },

        /**
         * Breadcrumb button press event handler. Render all the childs of an XBlock.
         *
         * @param {any} newParentIndex  Index of a parent XBlock
         */
        handleBreadcrumbButtonPress: function(newParentIndex) {
            this.renderXBlockInfo('backward', newParentIndex);
        },

        /**
         * Render XBlocks based on `forward` or `backward` navigation.
         *
         * @param {any} direction           `forward` or `backward`
         * @param {any} newParentIndex      Index of a parent XBlock
         */
        renderXBlockInfo: function(direction, newParentIndex) {
            if (direction === undefined) {
                this.parentInfo.parent = this.model;
            } else if (direction === 'forward') {
                // clicked child is the new parent
                this.parentInfo.parent = this.childrenInfo.children[newParentIndex];
            } else if (direction === 'backward') {
                // new parent will be one of visitedAncestors
                this.parentInfo.parent = this.visitedAncestors[newParentIndex];
                // remove visited ancestors
                this.visitedAncestors.splice(newParentIndex);
            }

            this.visitedAncestors.push(this.parentInfo.parent);

            if (this.parentInfo.parent.get('child_info')) {
                this.childrenInfo.children = this.parentInfo.parent.get('child_info').children;
            } else {
                this.childrenInfo.children = [];
            }

            this.setDisplayedXBlocksCategories();
            this.render();
        },

        /**
         * Set parent and child XBlock categories.
         */
        setDisplayedXBlocksCategories: function() {
            this.parentInfo.category = XBlockUtils.getXBlockType(
                this.parentInfo.parent.get('category'),
                this.visitedAncestors[this.visitedAncestors.length - 2]
            );
            this.childrenInfo.category = this.categoryRelationMap[this.parentInfo.category];
        },

        /**
         * Get index of source XBlock.
         *
         * @returns {any} Integer or undefined
         */
        getCurrentLocationIndex: function() {
            var category, ancestorXBlock, currentLocationIndex;

            if (this.childrenInfo.category === 'component' || this.childrenInfo.children.length === 0) {
                return currentLocationIndex;
            }

            category = this.childrenInfo.children[0].get('category');
            ancestorXBlock = _.find(
                this.ancestorInfo.ancestors, function(ancestor) { return ancestor.category === category; }
            );

            if (ancestorXBlock) {
                _.each(this.childrenInfo.children, function(xblock, index) {
                    if (ancestorXBlock.display_name === xblock.get('display_name') &&
                        ancestorXBlock.id === xblock.get('id')) {
                        currentLocationIndex = index;
                    }
                });
            }

            return currentLocationIndex;
        },

        /**
         * Get category text for currently displayed children.
         *
         * @returns {String}
         */
        getCategoryText: function() {
            return this.categoriesText[this.childrenInfo.category];
        },

        /**
         * Get text when a parent XBlock has no children.
         *
         * @returns {String}
         */
        getNoChildText: function() {
            return StringUtils.interpolate(
                gettext('This {parentCategory} has no {childCategory}'),
                {
                    parentCategory: this.parentInfo.category,
                    childCategory: this.categoriesText[this.childrenInfo.category].toLowerCase()
                }
            );
        },

        /**
         * Construct breadcurmb info.
         *
         * @returns {Object}
         */
        breadcrumbInfo: function() {
            return {
                breadcrumbs: _.map(this.visitedAncestors, function(ancestor) {
                    return ancestor.get('category') === 'course' ?
                           gettext('Course Outline') : ancestor.get('display_name');
                })
            };
        }
    });

    return XBlockListView;
});
