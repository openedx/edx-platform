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
    
    //NOTE:
    // Genex uses six global functions:
    // genexSetDNASequence (exported from GWT)
    // genexSetClickEvent (exported from GWT)
    // genexSetKeyEvent (exported from GWT)
    // genexSetProblemNumber (exported from GWT)
    //
    // It calls genexIsReady with a deferred command when it has finished 
    // initialization and has drawn itself
    // genexStoreAnswer(answer) is called when the GWT [Store Answer] button
    // is clicked
    
    genexIsReady = function() {
        //Load DNA sequence
        var dna_sequence = $('#dna_sequence').val();
        genexSetDNASequence(dna_sequence);
        //Now load mouse and keyboard handlers
        genexSetClickEvent();
        genexSetKeyEvent();
        //Now load problem
        var genex_problem_number = $('#genex_problem_number').val();
        genexSetProblemNumber(genex_problem_number);    
    };
    genexStoreAnswer = function(ans) {
        alert(ans);
    };
}).call(this);

