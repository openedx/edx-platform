/**
 * This class defines an edit view for groups within content experiment group configurations.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/baseview', 'underscore', 'underscore.string', 'gettext'
],
function(BaseView, _, str, gettext) {
    'use strict';
    _.str = str; // used in template
    var ExperimentGroupEditView = BaseView.extend({
        tagName: 'li',
        events: {
            'click .action-close': 'removeGroup',
            'change .group-name': 'changeName',
            'focus .groups-fields input': 'onFocus',
            'blur .groups-fields input': 'onBlur'
        },

        className: function() {
            var index = this.model.collection.indexOf(this.model);
            return 'field-group group group-' + index;
        },

        initialize: function() {
            this.template = this.loadTemplate('group-edit');
            this.listenTo(this.model, 'change', this.render);
        },

        render: function() {
            var collection = this.model.collection,
                index = collection.indexOf(this.model);

            this.$el.html(this.template({
                name: this.model.escape('name'),
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
