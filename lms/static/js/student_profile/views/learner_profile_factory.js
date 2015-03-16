;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone',
        'js/student_profile/views/learner_profile_view',
        'js/student_profile/views/learner_profile_photo_view'
    ], function (gettext, $, _, Backbone, LearnerProfileView, LearnerProfilePhotoView) {

        var setupLearnerProfile = function (profileData) {

            var learnerProfileElement = $('.learner-profile-container');
            var learnerProfilePhotoView = new LearnerProfilePhotoView({});

            var learnerProfileView = new LearnerProfileView({
                el: learnerProfileElement,
                profileData: profileData,
                profilePohotView: learnerProfilePhotoView
            });

            // TODO! Fetch values into model once profile API is available
            learnerProfileView.render();
        };

        return setupLearnerProfile;
    })
}).call(this, define || RequireJS.define);