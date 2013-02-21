(function () {
    console.log('annotation input loaded: ', this);
    var update = function() {
             alert("o hi");
    };

    var inputs = $('.annotation-input input');
    // update on load
    inputs.each(update); 
    // and on every change
    inputs.bind("input", update);
}).call(this);
