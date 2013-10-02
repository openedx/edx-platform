/**
 * File: lti.js
 *
 * Purpose: LTI module constructor. Given an LTI element, we process it.
 *
 *
 * Inside the element there is a form. If that form has a valid action
 * attribute, then we do one of:
 *
 *     1.) Submit the form. The results will be shown on the current page in an
 *         iframe.
 *     2.) Attach a handler function to a link which will submit the form. The
 *         results will be shown in a new window.
 *
 * The 'open_in_a_new_page' data attribute of the LTI element dictates which of
 * the two actions will be performed.
 */

/*
 * So the thing to do when working on a motorcycle, as in any other task, is to
 * cultivate the peace of mind which does not separate one's self from one's
 * surroundings. When that is done successfully, then everything else follows
 * naturally. Peace of mind produces right values, right values produce right
 * thoughts. Right thoughts produce right actions and right actions produce
 * work which will be a material reflection for others to see of the serenity
 * at the center of it all.
 *
 * ~ Robert M. Pirsig
 */

window.LTI = (function () {
    // Function initialize(element)
    //
    // Initialize the LTI module.
    //
    // @param element    DOM element, or jQuery element object.
    //
    // @return    undefined
    function initialize(element) {
        var form, openInANewPage, formAction;

        // In cms (Studio) the element is already a jQuery object. In lms it is
        // a DOM object.
        //
        // To make sure that there is no error, we pass it through the $()
        // function. This will make it a jQuery object if it isn't already so.
        element = $(element);

        form = element.find('.ltiLaunchForm');
        formAction = form.attr('action');

        // If action is empty string, or action is the default URL that should
        // not cause a form submit.
        if (!formAction || formAction === 'http://www.example.com') {

            // Nothing to do - no valid action provided. Error message will be
            // displaced in browser (HTML).
            return;
        }

        // We want a Boolean 'true' or 'false'. First we will retrieve the data
        // attribute, and then we will parse it via native JSON.parse().
        openInANewPage = element.find('.lti').data('open_in_a_new_page');
        openInANewPage = JSON.parse(openInANewPage);

        // If the Form's action attribute is set (i.e. we can perform a normal
        // submit), then we (depending on instance settings) submit the form
        // when user will click on a link, or submit the form immediately.
        if (openInANewPage === true) {
            element.find('.link_lti_new_window').on('click', function () {
                form.submit();
            });
        } else {
            // At this stage the form exists on the page and has a valid
            // action. We are safe to submit it, even if `openInANewPage` is
            // set to some weird value.
            //
            // Best case scenario is that `openInANewPage` is set to `true`.
            form.submit();
        }
    }

    return initialize;
}());
