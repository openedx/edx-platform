(function () {
    console.log('annotation input loaded: ', this);
    var update = function() {
             console.log("annotation input update");
    };

    var inputs = $('.annotation-input input');
    // update on load
    inputs.each(update); 
    // and on every change
    inputs.bind("input", update);
}).call(this);
