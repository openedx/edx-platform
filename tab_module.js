var tab_funcs=[]

##  We'd like to refresh the contents of tabs when they're shown again, but this probably 
##  isn't the way
## % for t in tabs:
##     % if 'js' in t[1]:
##       tab_funcs.push(function(){ ${t[1]['js']} });
##     % else:
##       tab_funcs.push(function(){});
##     % endif
## % endfor


$("#tabs").tabs({select:function(event, ui){
##	    tab_funcs[ui.index]();
	}});
