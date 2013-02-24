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
    // Genex uses four global functions:
    // genexSetDNASequence (exported from GWT)
    // genexSetClickEvent (exported from GWT)
    // genexSetKeyEvent (exported from GWT)
    // It calls genexIsReady with a deferred command when it has finished 
    // initialization and has drawn itself
    genexIsReady = function() {
        //Load DNA sequence
        var dna_sequence = $('#dna_sequence').val();
        genexSetDNASequence(dna_sequence);
        //Now load mouse and keyboard handlers
        genexSetClickEvent();
        genexSetKeyEvent();            
    };
}).call(this);

