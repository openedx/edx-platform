define(
    ['backbone', 'underscore', 'underscore.string', 'js/utils/module'],
function(Backbone, _, str, ModuleUtils) {
    'use strict';
    var XBlockInfo = Backbone.Model.extend({

        urlRoot: ModuleUtils.urlRoot,

        // NOTE: 'publish' is not an attribute on XBlockInfo, but it is used to signal the publish
        // and discard changes actions. Therefore 'publish' cannot be introduced as an attribute.
        defaults: {
            'id': null,
            'display_name': null,
            'category': null,
            'data': null,
            'metadata' : null,
            /**
             * The Studio URL for this xblock, or null if it doesn't have one.
             */
            'studio_url': null,
            /**
             * An optional object with information about the children as well as about
             * the primary xblock type that is supported as a child.
             */
            'child_info': null,
            /**
             * An optional object with information about each of the ancestors.
             */
            'ancestor_info': null,
            /**
             * Date of the last edit to this xblock or any of its descendants.
             */
            'edited_on':null,
            /**
             * User who last edited the xblock or any of its descendants.
             */
            'edited_by':null,
            /**
             * True iff a published version of the xblock exists.
             */
            "published": null,
            /**
             * Date of the last publish of this xblock, or null if never published.
             */
            'published_on': null,
            /**
             * User who last published the xblock, or null if never published.
             */
            'published_by': null,
            /**
             * True if the xblock has changes.
             * Note: this is not always provided as a performance optimization. It is only provided for
             * verticals functioning as units.
             */
            "has_changes": null,
            /**
             * Represents the possible publish states for an xblock. See the documentation
             * for XBlockVisibility to see a comprehensive enumeration of the states.
             */
            "visibility_state": null,
            /**
             * True if the release date of the xblock is in the past.
             */
            'released_to_students': null,
            /**
             * If the xblock is published, the date on which it will be released to students.
             * This can be null if the release date is unscheduled.
             */
            'release_date': null,
            /**
             * The xblock which is determining the release date. For instance, for a unit,
             * this will either be the parent subsection or the grandparent section.
             * This can be null if the release date is unscheduled.
             */
            'release_date_from':null,
            /**
             * True if this xblock is currently visible to students. This is computed server-side
             * so that the logic isn't duplicated on the client.
             */
            'currently_visible_to_students': null,
            /**
             * If xblock is graded, the date after which student assessment will be evaluated.
             * It has same format as release date, for example: 'Jan 02, 2015 at 00:00 UTC'.
             */
            'due_date': null,
            /**
             * Grading policy for xblock.
             */
            'format': null,
            /**
             * List of course graders names.
             */
            'course_graders': null,
            /**
             * True if this xblock contributes to the final course grade.
             */
            'graded': null,
            /**
             * The same as `release_date` but as an ISO-formatted date string.
             */
            'start': null,
            /**
             * The same as `due_date` but as an ISO-formatted date string.
             */
            'due': null,
            /**
             * True iff this xblock is explicitly staff locked.
             */
            'has_explicit_staff_lock': null,
            /**
             * True iff this any of this xblock's ancestors are staff locked.
             */
            'ancestor_has_staff_lock': null,
            /**
             * The xblock which is determining the staff lock value. For instance, for a unit,
             * this will either be the parent subsection or the grandparent section.
             * This can be null if the xblock has no inherited staff lock.
             */
            'staff_lock_from': null,
            /**
             * True iff this xblock should display a "Contains staff only content" message.
             */
            'staff_only_message': null
        },

        initialize: function () {
            // Extend our Model by helper methods.
            _.extend(this, this.getCategoryHelpers());
        },

        parse: function(response) {
            if (response.ancestor_info) {
                response.ancestor_info.ancestors = this.parseXBlockInfoList(response.ancestor_info.ancestors);
            }
            if (response.child_info) {
                response.child_info.children = this.parseXBlockInfoList(response.child_info.children);
            }
            return response;
        },

        parseXBlockInfoList: function(list) {
            return _.map(list, function(item) {
                return this.createChild(item);
            }, this);
        },

        createChild: function(response) {
            return new XBlockInfo(response, { parse: true });
        },

        hasChildren: function() {
            var childInfo = this.get('child_info');
            return childInfo && childInfo.children.length > 0;
        },

        isPublishable: function(){
            return !this.get('published') || this.get('has_changes');
        },

        /**
         * Return a list of convenience methods to check affiliation to the category.
         * @return {Array}
         */
        getCategoryHelpers: function () {
            var categories = ['course', 'chapter', 'sequential', 'vertical'],
                helpers = {};

            _.each(categories, function (item) {
                helpers['is' + str.titleize(item)] = function () {
                    return this.get('category') === item;
                };
            }, this);

            return helpers;
        },

        /**
         * Check if we can edit current XBlock or not on Course Outline page.
         * @return {Boolean}
         */
        isEditableOnCourseOutline: function() {
            return this.isSequential() || this.isChapter() || this.isVertical();
        }
    });
    return XBlockInfo;
});
