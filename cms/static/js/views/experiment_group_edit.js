/**
 * This class defines an edit view for groups within content experiment group configurations.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/baseview', 'underscore', 'underscore.string', 'gettext', 'text!templates/group-edit.underscore'
],
function(BaseView, _, str, gettext, groupEditTemplate) {
    'use strict';
    var ExperimentGroupEditView = BaseView.extend({
        tagName: 'li',
        events: {
            'click .action-close': 'removeGroup',
            'change .group-name': 'changeName',
            'focus .group-name': 'onFocus',
            'blur .group-name': 'onBlur'
        },

        className: function() {
            var index = this.model.collection.indexOf(this.model);
            return 'field-group group group-' + index;
        },

        initialize: function() {
            this.listenTo(this.model, 'change', this.render);
        },

        render: function() {
            var collection = this.model.collection,
                index = collection.indexOf(this.model);

            this.$el.html(_.template(groupEditTemplate)({
                name: this.model.get('name'),
                allocation: this.getAllocation(),
                index: index,
                error: this.model.validationError
            }));

            return this;
        },

        changeName: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set({
                name: this.$('.group-name').val()
            }, { silent: true });

            return this;
        },

        removeGroup: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.collection.remove(this.model);
            return this.remove();
        },

        getAllocation: function() {
            return Math.floor(100 / this.model.collection.length);
        },

        onFocus: function () {
            this.$el.closest('.groups-fields').addClass('is-focused');
        },

        onBlur: function () {
            this.$el.closest('.groups-fields').removeClass('is-focused');
        }
    });

    return ExperimentGroupEditView;
});
