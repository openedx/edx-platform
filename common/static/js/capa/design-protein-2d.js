(function () {
    var timeout = 1000;

    function initializeApplet(applet) {
        console.log("Initializing " + applet);
        waitForApplet(applet);
    }

    function waitForApplet(applet) {
        if (applet.isActive && applet.isActive()) {
            console.log("Applet is ready.");
            var answerStr = applet.checkAnswer();
            console.log(answerStr);
            var input = $('.designprotein2dinput input');
            console.log(input);
            input.val(answerStr);
        } else if (timeout > 30 * 1000) {
            console.error("Applet did not load on time.");
        } else {
            console.log("Waiting for applet...");
            setTimeout(function() { waitForApplet(applet); }, timeout);
        }
    }
    
    var applets = $('.designprotein2dinput object');
    applets.each(function(i, el) { initializeApplet(el); });
}).call(this);
