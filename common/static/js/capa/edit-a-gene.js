(function () {
    var timeout = 1000;

    waitForGenex();

    function waitForGenex() {
        if (typeof(genex) !== "undefined" && genex) {
            genex.onInjectionDone("genex");
        }
        else {
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
    
    //Genex does not call the following function
    genexGetInputField = function() {
        var problem = $('#genex_container').parents('.problem');
        return problem.find('input[type="hidden"][name!="genex_dna_sequence"][name!="genex_problem_number"]');
    };     
    
    genexIsReady = function() {
        var input_field = genexGetInputField();
        var genex_saved_state = input_field.val();
        var genex_default_dna_sequence;
        var genex_dna_sequence;
        
        //Get the DNA sequence from xml file
        genex_default_dna_sequence = $('#genex_dna_sequence').val();
        //Set the default DNA
        genexSetDefaultDNASequence(genex_default_dna_sequence);
        
        //Now load problem
        var genex_problem_number = $('#genex_problem_number').val();
        genexSetProblemNumber(genex_problem_number);
        
        //Set the DNA sequence that is displayed
        if (genex_saved_state === '') {
            //Load DNA sequence from xml file 
            genex_dna_sequence = genex_default_dna_sequence;
        }
        else {
            //Load DNA sequence from saved value
            genex_saved_state = JSON.parse(genex_saved_state);
            genex_dna_sequence = genex_saved_state.genex_dna_sequence;
        }
        genexSetDNASequence(genex_dna_sequence);
        
        //Now load mouse and keyboard handlers
        genexSetClickEvent();
        genexSetKeyEvent();
    };
    
    genexStoreAnswer = function(answer) {
        var input_field = genexGetInputField();
        var value = {'genex_dna_sequence': genexGetDNASequence(), 'genex_answer': answer};
        input_field.val(JSON.stringify(value));
    };
}).call(this);