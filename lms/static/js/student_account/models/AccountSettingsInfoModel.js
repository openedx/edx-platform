var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccountSettingsInfoModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            username: '',
            fullname: '',
            email: '',
            password: '',
            language: ''
        }
    });
}).call(this, Backbone);
