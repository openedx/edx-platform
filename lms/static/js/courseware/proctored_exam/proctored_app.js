$(function() {
    var proctored_exam_view = new edx.coursware.proctored_exam.ProctoredExamView({
        el: $(".proctored_exam_status"),
        proctored_template: '#proctored-exam-status-tpl',
        model: new ProctoredExamModel()
    });
    proctored_exam_view.render();
});