;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Model.extend({
        defaults: {
            name: '',
            due_date: '',
            url: ''
        }
    });

});

})(define || RequireJS.define);
