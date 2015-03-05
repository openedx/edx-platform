var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccountSettingsModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            username: '',
            name: '',
            email: '',
            password: '',
            language: '',
            country: null,
            date_joined: "",
            gender: null,
            goals: "",
            level_of_education: null,
            mailing_address: "",
            year_of_birth: null
        }
    });
}).call(this, Backbone);
