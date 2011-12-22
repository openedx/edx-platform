// IMPORTANT TODO: Namespace

var ${ id }contents=["",
 %for t in items:
 ${t[1]['content']} , 
 %endfor
 ""
       ];

var ${ id }types=["",
 %for t in items:
 "${t[1]['type']}" , 
 %endfor
 ""
       ];

var ${ id }init_functions=["",
 %for t in items:
	       function(){ ${t[1]['init_js']} }, 
 %endfor
	       ""];

var ${ id }destroy_functions=["",
 %for t in items:
	       function(){ ${t[1]['destroy_js']} }, 
 %endfor
	       ""];

var ${ id }loc = -1;

function ${ id }goto(i) {
    if (${ id }loc!=-1)
	${ id }destroy_functions[ ${ id }loc ]();
    $('#seq_content').html(${ id }contents[i]);
    ${ id }init_functions[i]()
	       //$('#tt_'+${ id }loc).attr("style", "background-color:gray");
	       $('#tt_'+${ id }loc).removeClass();
	       $('#tt_'+${ id }loc).addClass("seq_"+${ id }types[${ id }loc]+"_visited");
    ${ id }loc=i;
    //$('#tt_'+i).attr("style", "background-color:red");
    $('#tt_'+i).removeClass();
    $('#tt_'+i).addClass("seq_active");

    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
}

function ${ id }setup_click(i) {
        $('#tt_'+i).click(function(eo) { ${ id }goto(i);});
	$('#tt_'+i).addClass("seq_"+${ id }types[i]+"_inactive");

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
	for(i=1; i<${ len(items)+1 }; i++) {
	    ${ id }setup_click(i);
	}
        $('#${ id }next').click(function(eo) { ${ id }next();});
        $('#${ id }prev').click(function(eo) { ${ id }prev();});
	${ id }goto(1);
    });
