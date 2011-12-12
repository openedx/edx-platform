// CRITICAL TODO: Namespace

var files=["",
 %for t in items:
 ${t[1]['content']} , 
 %endfor
 ""
       ];

var functions=["",
 %for t in items:
	       function(){ ${t[1]['js']} }, 
 %endfor
	       ""];

var loc;

function goto(i) {
    $('#content').html(files[i]);
    functions[i]()
    loc=i;
}

function setup_click(i) {
        $('#tt_'+i).click(function(eo) { goto(i);});
}

function next() { 
    loc=loc+1;
    if(loc> ${ len(items) } ) loc=${ len(items) };
    goto(loc);
}

function prev() { 
    loc=loc-1;
    if(loc<1) loc=1;
    goto(loc);
}

$(function() {
	var i; 
	for(i=1; i<11; i++) {
	    setup_click(i);
	}
        $('#next').click(function(eo) { next();});
        $('#prev').click(function(eo) { prev();});
	goto(1);
    });
