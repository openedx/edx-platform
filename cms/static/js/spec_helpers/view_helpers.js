/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery"],
    function($) {
        var feedbackTemplate = readFixtures('system-feedback.underscore'),
            installViewTemplates;

        installViewTemplates = function(append) {
            if (append) {
                appendSetFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTemplate));
            } else {
                setFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTemplate));
            }
        };

        return {
            'installViewTemplates': installViewTemplates
        };
    });
