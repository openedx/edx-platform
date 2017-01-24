(function() {
    'use strict';
    /**
     * This function will process all the attributes from the DOM element passed, taking all of
     * the configuration attributes. It uses the request-username and request-email
     * to prompt the user to decide if they want to share their personal information
     * with the third party application connecting through LTI.
     * @constructor
     * @param {jQuery} element DOM element with the lti container.
     */
    this.LTI = function(element) {
        var dataAttrs = $(element).find('.lti').data(),
            askToSendUsername = (dataAttrs.askToSendUsername === 'True'),
            askToSendEmail = (dataAttrs.askToSendEmail === 'True');

        // When the lti button is clicked, provide users the option to
        // accept or reject sending their information to a third party
        $(element).on('click', '.link_lti_new_window', function() {
            if (askToSendUsername && askToSendEmail) {
                return confirm(gettext('Click OK to have your username and e-mail address sent to a 3rd party application.\n\nClick Cancel to return to this page without sending your information.'));
            } else if (askToSendUsername) {
                return confirm(gettext('Click OK to have your username sent to a 3rd party application.\n\nClick Cancel to return to this page without sending your information.'));
            } else if (askToSendEmail) {
                return confirm(gettext('Click OK to have your e-mail address sent to a 3rd party application.\n\nClick Cancel to return to this page without sending your information.'));
            } else {
                return true;
            }
        });
    };
}).call(this);
