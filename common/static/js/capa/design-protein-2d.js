(function() {
    var timeout = 1000;

    waitForProtex();

    function waitForProtex() {
        // eslint-disable-next-line no-undef
        if (typeof protex !== 'undefined' && protex) {
            // eslint-disable-next-line no-undef
            protex.onInjectionDone('protex');
        // eslint-disable-next-line brace-style
        }
        /* if (typeof(protex) !== "undefined") {
            //initializeProtex();
        } */
        else {
            setTimeout(function() { waitForProtex(); }, timeout);
        }
    }

    // NOTE:
    // Protex uses three global functions:
    // protexSetTargetShape (exported from GWT)
    // exported protexCheckAnswer (exported from GWT)
    // It calls protexIsReady with a deferred command when it has finished
    // initialization and has drawn itself

    function updateProtexField() {
        var problem = $('#protex_container').parents('.problem');
        // eslint-disable-next-line camelcase
        var input_field = problem.find('input[type=hidden]');
        /* eslint-disable-next-line camelcase, no-undef */
        var protex_answer = protexCheckAnswer();
        // eslint-disable-next-line camelcase
        var value = {protex_answer: protex_answer};
        // console.log(JSON.stringify(value));
        // eslint-disable-next-line camelcase
        input_field.val(JSON.stringify(value));
    }

    // eslint-disable-next-line no-undef
    protexIsReady = function() {
        // Load target shape
        // eslint-disable-next-line camelcase
        var target_shape = $('#target_shape').val();
        // eslint-disable-next-line no-undef
        protexSetTargetShape(target_shape);

        // Get answer from protex and store it into the hidden input field
        // when Check button is clicked
        // eslint-disable-next-line camelcase
        var $fold_button = $('#fold-button');
        // eslint-disable-next-line camelcase
        $fold_button.on('click', function() {
            var problem = $('#protex_container').parents('.problem');
            // eslint-disable-next-line camelcase
            var input_field = problem.find('input[type=hidden]');
            /* eslint-disable-next-line camelcase, no-undef */
            var protex_answer = protexCheckAnswer();
            // eslint-disable-next-line camelcase
            var value = {protex_answer: protex_answer};
            // console.log(JSON.stringify(value));
            // eslint-disable-next-line camelcase
            input_field.val(JSON.stringify(value));
        });
        updateProtexField();
    };

    /* function initializeProtex() {
        //Check to see if the two exported GWT functions protexSetTargetShape
        // and protexCheckAnswer have been appended to global scope -- this
        //happens at the end of onModuleLoad() in GWT
        if (typeof(protexSetTargetShape) === "function" &&
            typeof(protexCheckAnswer) === "function") {

            //Load target shape
            var target_shape = $('#target_shape').val();
            //protexSetTargetShape(target_shape);

            //Get answer from protex and store it into the hidden input field
            //when Check button is clicked
            var problem = $('#protex_container').parents('.problem');
            var check_button = problem.find('input.check');
            var input_field = problem.find('input[type=hidden]');
            check_button.on('click', function() {
                var protex_answer = protexCheckAnswer();
                var value = {protex_answer: protex_answer};
                input_field.val(JSON.stringify(value));
            });

            //TO DO: Fix this, it works but is utterly ugly and unreliable
            setTimeout(function() {
              protexSetTargetShape(target_shape);}, 2000);

        }
        else {
            setTimeout(function() {initializeProtex(); }, timeout);
        }
    } */
}).call(this);
