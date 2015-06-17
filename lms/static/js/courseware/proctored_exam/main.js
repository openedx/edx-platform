RequireJS.require([
    'jquery',
    'backbone',
    'js/courseware/proctored_exam/proctored_app',
    'js/courseware/base/models/proctored_exam_model',
    'js/courseware/base/views/proctored_exam_view'
], function ($, Backbone, ProctoredApp, ProctoredExamModel, ProctoredExamView) {
    'use strict';
    var app = new ProctoredApp(
        ProctoredExamModel,
        ProctoredExamView
    );
});
