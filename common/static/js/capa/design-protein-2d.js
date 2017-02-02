(function() {
    var timeout = 1000;

    waitForProtex();

    function waitForProtex() {
        if (typeof(protex) !== 'undefined' && protex) {
            protex.onInjectionDone('protex');
        }
        /* if (typeof(protex) !== "undefined") {
            //initializeProtex();
        }*/
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
        var input_field = problem.find('input[type=hidden]');
        var protex_answer = protexCheckAnswer();
        var value = {protex_answer: protex_answer};
            // console.log(JSON.stringify(value));
        input_field.val(JSON.stringify(value));
    }

    protexIsReady = function() {
        // Load target shape
        var target_shape = $('#target_shape').val();
        protexSetTargetShape(target_shape);

        // Get answer from protex and store it into the hidden input field
        // when Check button is clicked
        var fold_button = $('#fold-button');
        fold_button.on('click', function() {
            var problem = $('#protex_container').parents('.problem');
            var input_field = problem.find('input[type=hidden]');
            var protex_answer = protexCheckAnswer();
            var value = {protex_answer: protex_answer};
            // console.log(JSON.stringify(value));
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
    }*/
}).call(this);
