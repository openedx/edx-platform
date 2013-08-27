window.LTI = (function () {
    var LTI;

    // Function LTI()
    //
    // The LTI module constructor. It will be called by XModule for any
    // LTI module DIV that is found on the page.
    LTI = function (element) {
        $(document).ready(function () {
            LTI.init(element);
        });
    }

    // Function init()
    //
    // Initialize the LTI iframe.
    LTI.init = function (element) {
        var form, frame;

        // In cms (Studio) the element is already a jQuery object. In lms it is
        // a DOM object.
        //
        // To make sure that there is no error, we pass it through the $()
        // function. This will make it a jQuery object if it isn't already so.
        element = $(element);

        form = element.find('#ltiLaunchForm');
        frame = element.find('#ltiLaunchFrame');

        // If the Form's action attribute is set (i.e. we can perform a normal
        // submit), then we submit the form and make it big enough so that the
        // received response can fit in it. Hide the error message, if shown.
        if (form.attr('action')) {
            form.submit();

            element.find('.error_message').addClass('hidden');
            frame.show();
            frame.width('100%').height(800);
        }

        // If no action URL was specified, we show an error message.
        else {
            frame.hide();
            element.find('.error_message').removeClass('hidden');
        }
    }

    return LTI;
}());
