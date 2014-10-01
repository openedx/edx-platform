define(['gettext', 'js/views/feedback_prompt'], function(gettext, PromptView) {
    'use strict';
    return function (hasUnit, editUnitUrl, courseHomeUrl, errMsg) {
        var dialog;
        if(hasUnit) {
            dialog = new PromptView({
                title: gettext('There has been an error while exporting.'),
                message: gettext('There has been a failure to export to XML at least one component. It is recommended that you go to the edit page and repair the error before attempting another export. Please check that all components on the page are valid and do not display any error messages.'),
                intent: 'error',
                actions: {
                    primary: {
                        text: gettext('Correct failed component'),
                        click: function(view) {
                            view.hide();
                            document.location = editUnitUrl;
                        }
                    },
                    secondary: {
                        text: gettext('Return to Export'),
                        click: function(view) {
                            view.hide();
                        }
                    }
                }
            });
        } else {
            var msg = '<p>' + gettext('There has been a failure to export your course to XML. Unfortunately, we do not have specific enough information to assist you in identifying the failed component. It is recommended that you inspect your courseware to identify any components in error and try again.') + '</p><p>' + gettext('The raw error message is:') + '</p>' + errMsg;
            dialog = new PromptView({
                title: gettext('There has been an error with your export.'),
                message: msg,
                intent: 'error',
                actions: {
                    primary: {
                        text: gettext('Yes, take me to the main course page'),
                        click: function(view) {
                            view.hide();
                            document.location = courseHomeUrl;
                        }
                    },
                    secondary: {
                        text: gettext('Cancel'),
                        click: function(view) {
                          view.hide();
                        }
                    }
                }
            });
        }

        // The CSS animation for the dialog relies on the 'js' class
        // being on the body. This happens after this JavaScript is executed,
        // causing a 'bouncing' of the dialog after it is initially shown.
        // As a workaround, add this class first.
        $('body').addClass('js');
        dialog.show();
    };
});
