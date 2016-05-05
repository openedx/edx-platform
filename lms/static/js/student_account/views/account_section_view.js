;(function (define, undefined) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'backbone',
        'text!templates/student_account/account_settings_section.underscore'
    ], function (gettext, $, _, Backbone, sectionTemplate) {

        var AccountSectionView = Backbone.View.extend({

            initialize: function (options) {
                this.options = options;
            },

            render: function () {
                this.$el.html(_.template(sectionTemplate)({
                    sections: this.options.sections
                }));
            }
        });

        return AccountSectionView;
    });
}).call(this, define || RequireJS.define);
