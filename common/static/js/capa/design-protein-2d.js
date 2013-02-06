(function () {
    var timeout = 1000;

    function initializeApplet(applet) {
        console.log("Initializing " + applet);
        waitForApplet(applet);
    }

    function waitForApplet(applet) {
        if (applet.isActive && applet.isActive()) {
            console.log("Applet is ready.");

            // FIXME: [rocha] This is a hack to capture the click on the check
            // button and update the hidden field with the applet values
            var input_field = $('.designprotein2dinput input');

            var problem = $(applet).parents('.problem');
            var check_button = problem.find('input.check');
            check_button.on('click', function() {
                var answerStr = applet.checkAnswer();
                console.log(answerStr);
                input_field.val(answerStr);
            });

        } else {
            console.log("Waiting for applet...");
            setTimeout(function() { waitForApplet(applet); }, timeout);
        }
    }

    var applets = $('.designprotein2dinput object');
    applets.each(function(i, el) { initializeApplet(el); });

}).call(this);
