var files=["",
 %for t in items:
 ${t[1]['content']} , 
 %endfor
 ""
       ];

var loc;

function goto(i) {
    $('#content').html(files[i]);
    loc=i;
}

function setup_click(i) {
    $.get(i+'.html', function(data){
	    files[i]=data;
        })
        $('#tt_'+i).click(function(eo) { goto(i);});
}

function next() { 
    loc=loc+1;
    if(loc>10) loc=10;
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
    });

$('#debug').text('loaded');