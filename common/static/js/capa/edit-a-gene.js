(function() {
    var timeout = 1000;

    waitForGenex();

    function waitForGenex() {
        // eslint-disable-next-line no-undef
        if (typeof genex !== 'undefined' && genex) {
            // eslint-disable-next-line no-undef
            genex.onInjectionDone('genex');
        } else {
            setTimeout(function() { waitForGenex(); }, timeout);
        }
    }

    // NOTE:
    // Genex uses 8 global functions, all prefixed with genex:
    // 6 are exported from GWT:
    // genexSetDefaultDNASequence
    // genexSetDNASequence
    // genexGetDNASequence
    // genexSetClickEvent
    // genexSetKeyEvent
    // genexSetProblemNumber
    //
    // It calls genexIsReady with a deferred command when it has finished
    // initialization and has drawn itself
    // genexStoreAnswer(answer) is called each time the DNA sequence changes
    // through user interaction

    // Genex does not call the following function
    // eslint-disable-next-line no-undef
    genexGetInputField = function() {
        var problem = $('#genex_container').parents('.problem');
        return problem.find('input[type="hidden"][name!="genex_dna_sequence"][name!="genex_problem_number"]');
    };

    // eslint-disable-next-line no-undef
    genexIsReady = function() {
        /* eslint-disable-next-line camelcase, no-undef */
        var input_field = genexGetInputField();
        // eslint-disable-next-line camelcase
        var genex_saved_state = input_field.val();
        // eslint-disable-next-line camelcase
        var genex_default_dna_sequence;
        // eslint-disable-next-line camelcase
        var genex_dna_sequence;

        // Get the DNA sequence from xml file
        // eslint-disable-next-line camelcase
        genex_default_dna_sequence = $('#genex_dna_sequence').val();
        // Set the default DNA
        // eslint-disable-next-line no-undef
        genexSetDefaultDNASequence(genex_default_dna_sequence);

        // Now load problem
        // eslint-disable-next-line camelcase
        var genex_problem_number = $('#genex_problem_number').val();
        // eslint-disable-next-line no-undef
        genexSetProblemNumber(genex_problem_number);

        // Set the DNA sequence that is displayed
        // eslint-disable-next-line camelcase
        if (genex_saved_state === '') {
            // Load DNA sequence from xml file
            // eslint-disable-next-line camelcase
            genex_dna_sequence = genex_default_dna_sequence;
        } else {
            // Load DNA sequence from saved value
            // eslint-disable-next-line camelcase
            genex_saved_state = JSON.parse(genex_saved_state);
            // eslint-disable-next-line camelcase
            genex_dna_sequence = genex_saved_state.genex_dna_sequence;
        }
        // eslint-disable-next-line no-undef
        genexSetDNASequence(genex_dna_sequence);

        // Now load mouse and keyboard handlers
        // eslint-disable-next-line no-undef
        genexSetClickEvent();
        // eslint-disable-next-line no-undef
        genexSetKeyEvent();
    };

    // eslint-disable-next-line no-undef
    genexStoreAnswer = function(answer) {
        /* eslint-disable-next-line camelcase, no-undef */
        var input_field = genexGetInputField();
        // eslint-disable-next-line no-undef
        var value = {genex_dna_sequence: genexGetDNASequence(), genex_answer: answer};
        // eslint-disable-next-line camelcase
        input_field.val(JSON.stringify(value));
    };
}).call(this);
