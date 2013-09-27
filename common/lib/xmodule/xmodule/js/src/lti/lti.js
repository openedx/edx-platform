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
 *     2.) attach a handler function to a link which will submit the form. The
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
    function initialize(element) {
        var form, open_in_a_new_page;

        // In cms (Studio) the element is already a jQuery object. In lms it is
        // a DOM object.
        //
        // To make sure that there is no error, we pass it through the $()
        // function. This will make it a jQuery object if it isn't already so.
        element = $(element);

        form = element.find('.ltiLaunchForm');

        if (
            // Action is one of: null, undefined, 0, 000, '', false.
            !Boolean(form.attr('action')) ||

            // Default URL that should not cause a form submit.
            form.attr('action') === 'http://www.example.com'
        ) {
            return; // Nothing to do - no valid action provided.
        }

        // We want a Boolean 'true' or 'false'. First we will retrieve the data
        // attribute, and then we will parse it via native JSON.parse().
        open_in_a_new_page = element.find('.lti').data('open_in_a_new_page');
        try {
            open_in_a_new_page = JSON.parse(open_in_a_new_page);
        } catch (e) {
            console.log('ERROR: Parsing data attribute "open_in_a_new_page".');
            console.log('*** error = "' + e.toString() + '".');

            open_in_a_new_page = null;
        }

        // If the Form's action attribute is set (i.e. we can perform a normal
        // submit), then we submit the form immediately or when user will click
        // on a link (depending on instance settings) and make the frame shown.
        if (open_in_a_new_page === true) {
            element.find('.link_lti_new_window').on('click', function () {
                form.submit();
            });
        } else if (open_in_a_new_page === false) {
            form.submit();
        }
    }

    return initialize;
}());
