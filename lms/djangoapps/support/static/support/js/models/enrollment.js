(function(define) {
    'use strict';
    define(['backbone', 'underscore'], function(Backbone, _) {
        return Backbone.Model.extend({
            updateEnrollment: function(new_mode, reason) {
                return $.ajax({
                    url: this.url(),
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        course_id: this.get('course_id'),
                        new_mode: new_mode,
                        old_mode: this.get('mode'),
                        reason: reason
                    }),
                    success: _.bind(function(response) {
                        this.set('manual_enrollment', response);
                        this.set('mode', new_mode);
                    }, this)
                });
            }
        });
    });
}).call(this, define || RequireJS.define);
