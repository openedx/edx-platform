// CRITICAL TODO: Namespace

var ${ id }contents=["",
 %for t in items:
 ${t[1]['content']} , 
 %endfor
 ""
       ];

var ${ id }functions=["",
 %for t in items:
	       function(){ ${t[1]['init_js']} }, 
 %endfor
	       ""];

var ${ id }loc;

function ${ id }goto(i) {
    // TODO: 
    //    ${ id }contents[${ id }loc] = $('#content').html();
    $('#content').html(${ id }contents[i]);
    ${ id }functions[i]()
	       $('#tt_'+${ id }loc).attr("style", "background-color:grey");
    ${ id }loc=i;
    $('#tt_'+i).attr("style", "background-color:red");
    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
}

function ${ id }setup_click(i) {
        $('#tt_'+i).click(function(eo) { ${ id }goto(i);});
}

function ${ id }next() { 
    var i=${ id }loc+1;
    if(i > ${ len(items) } ) i = ${ len(items) };
    ${ id }goto(i);
}

function ${ id }prev() { 
    var i=${ id }loc-1;
    if (i < 1 ) i = 1;
    ${ id }goto(i);
}

$(function() {
	var i; 
	for(i=1; i<11; i++) {
	    ${ id }setup_click(i);
	}
        $('#${ id }next').click(function(eo) { ${ id }next();});
        $('#${ id }prev').click(function(eo) { ${ id }prev();});
	${ id }goto(1);
    });
