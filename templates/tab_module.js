// IMPORTANT TODO: Namespace

var ${ id }contents=["",
 %for t in items:
 ${t[1]['content']} , 
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
    $('#tabs-'+(i-1)).html(${ id }contents[i]);
    ${ id }init_functions[i]()
	       $('#tt_'+${ id }loc).attr("style", "background-color:grey");
    ${ id }loc=i;
    $('#tt_'+i).attr("style", "background-color:red");
    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
}

$("#tabs").tabs({select:function(event, ui){
	    //global=ui;
	    return true;
	},
        show:function(event,ui){
	    //global=ui;
	    ${ id }goto(ui.index+1);
	    return true;
        },
        });
