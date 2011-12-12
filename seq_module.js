// CRITICAL TODO: Namespace

var ${ id }files=["",
 %for t in items:
 ${t[1]['content']} , 
 %endfor
 ""
       ];

var ${ id }functions=["",
 %for t in items:
	       function(){ ${t[1]['js']} }, 
 %endfor
	       ""];

var ${ id }loc;

function ${ id }goto(i) {
    $('#content').html(${ id }files[i]);
    ${ id }functions[i]()
    ${ id }loc=i;
}

function ${ id }setup_click(i) {
        $('#tt_'+i).click(function(eo) { ${ id }goto(i);});
}

function ${ id }next() { 
    ${ id }loc=${ id }loc+1;
    if(${ id }loc> ${ len(items) } ) ${ id }loc=${ len(items) };
    ${ id }goto(${ id }loc);
}

function ${ id }prev() { 
    ${ id }loc=${ id }loc-1;
    if(${ id }loc<1) ${ id }loc=1;
    ${ id }goto(${ id }loc);
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
