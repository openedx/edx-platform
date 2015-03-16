;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'js/student_profile/views/learner_profile_view',
        'js/student_profile/views/learner_profile_image_view'
    ], function (gettext, $, _, Backbone, LearnerProfileView, LearnerProfileImageView) {

        var setupLearnerProfile = function (fieldsData) {

            var learnerProfileElement = $('.learner-profile-container');
            var learnerProfileImageView = new LearnerProfileImageView({});

            var learnerProfileView = new LearnerProfileView({
                el: learnerProfileElement,
                fieldsData: fieldsData,
                profileImageView: learnerProfileImageView
            });

            // TODO! Fetch values into model once profile API is available
            learnerProfileView.render();
        };

        return setupLearnerProfile;
    })
}).call(this, define || RequireJS.define);