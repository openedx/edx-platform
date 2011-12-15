var ${ id }files=["",
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

$("#tabs").tabs({select:function(event, ui){
	    global=ui;
	    return true;
	},
        show:function(event,ui){
	    global=ui;
	    alert('hello');
	    return true;
        },
        });
