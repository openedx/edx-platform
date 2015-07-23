/**
 * View that displays a card for a course.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'js/components/card/views/card'],
        function (Backbone, _, gettext, CardView) {
            var CourseCardView = CardView.extend({
                action: function (event) {
                    event.preventDefault();
                    window.alert("Navigate to the course!");
                },

                configuration: 'square_card',
                cardClass: 'course-card',
                title: function () { return this.model.get('name'); },
                actionClass: 'action-view',
                actionContent: function () {
                    var screenReaderText = _.escape(gettext('View Course'));
                    return '<span class="sr">' + screenReaderText + '</span><i class="icon fa fa-arrow-right" aria-hidden="true"></i>';
                }
            });

            return CourseCardView;
        });
}).call(this, define || RequireJS.define);
