;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'edx-ui-toolkit/js/utils/html-utils'], function (Backbone, _, HtmlUtils) {

        return Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                course_id: '',
                usage_id: '',
                display_name: '',
                path: [],
                created: ''
            },

            blockUrl: function () {
                return '/courses/' + encodeURIComponent(this.get('course_id')) + '/jump_to/' +
                    encodeURIComponent(this.get('usage_id'));
            },

            breadcrumbTrail: function () {
                var html = HtmlUtils.HTML(
                    ' <i class="icon fa fa-caret-right" aria-hidden="true"></i><span class="sr">-</span> '
                );
                var display_names = _.pluck(this.get('path'), 'display_name');
                display_names.push(this.get('display_name'));

                var breadcrumbs = display_names[0];
                for (var index = 1; index < display_names.length; index++) {
                    breadcrumbs = HtmlUtils.joinHtml(
                        breadcrumbs,
                        html,
                        display_names[index]
                    );
                }
                return breadcrumbs;
            }
        });
    });

})(define || RequireJS.define);
