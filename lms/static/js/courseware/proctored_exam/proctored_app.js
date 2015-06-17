;(function (define) {

define(['backbone'], function(Backbone) {
    'use strict';

    return function (ProctoredExamModel, ProctoredExamView) {
        var proctored_exam_view = new ProctoredExamView({
            el: $(".proctored_exam_status"),
            proctored_template: '#proctored_exams_status-tpl',
            model: new ProctoredExamModel()
        });
        proctored_exam_view.render();
    };

});

})(define || RequireJS.define);
