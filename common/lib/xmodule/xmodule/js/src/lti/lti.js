window.LTI = (function () {
    // Function initialize(element)
    //
    // Initialize the LTI iframe.
    function initialize(element) {
        var form;

        // In cms (Studio) the element is already a jQuery object. In lms it is
        // a DOM object.
        //
        // To make sure that there is no error, we pass it through the $()
        // function. This will make it a jQuery object if it isn't already so.
        element = $(element);

        form = element.find('.ltiLaunchForm');

        // If the Form's action attribute is set (i.e. we can perform a normal
        // submit), then we submit the form and make the frame shown.
        if (form.attr('action')) {
            form.submit();
            element.find('.lti').addClass('rendered')
        }
    }

    return initialize;
}());
