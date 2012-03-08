// IMPORTANT TODO: Namespace

var ${ id }contents=["",
 %for t in items:
 ${t['content']} , 
 %endfor
 ""
       ];

var ${ id }types=["",
 %for t in items:
 "${t['type']}" , 
 %endfor
 ""
       ];

var ${ id }init_functions=["",
 %for t in items:
	       function(){ ${t['init_js']} }, 
 %endfor
	       ""];

var ${ id }titles=${titles};

var ${ id }destroy_functions=["",
 %for t in items:
	       function(){ ${t['destroy_js']} }, 
 %endfor
	       ""];

var ${ id }loc = -1;
function disablePrev() { 
    var i=${ id }loc-1;
    log_event("seq_prev", {'old':${id}loc, 'new':i,'id':'${id}'});
    if (i < 1 ) {
      $('.${ id }prev a').addClass('disabled');
    } else {
      $('.${ id }prev a').removeClass('disabled');
    };
  }

  function disableNext() { 
    var i=${ id }loc+1;
    log_event("seq_next", {'old':${id}loc, 'new':i,'id':'${id}'});

    if(i > ${ len(items) } ) {
      $('.${ id }next a').addClass('disabled');
    } else {
      $('.${ id }next a').removeClass('disabled');
    };
}

function ${ id }goto(i) {
  log_event("seq_goto", {'old':${id}loc, 'new':i,'id':'${id}'});

  postJSON('/modx/sequential/${ id }/goto_position',
  {'position' : i });

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
  $('#tt_'+i).addClass("seq_"+${ id }types[${ id }loc]+"_active");

  MathJax.Hub.Queue(["Typeset",MathJax.Hub]);

  disableNext();
  disablePrev();
}

function ${ id }setup_click(i) {
        $('#tt_'+i).click(function(eo) { ${ id }goto(i);});
	$('#tt_'+i).addClass("seq_"+${ id }types[i]+"_inactive");
	$('#tt_'+i).parent().append("<p>" + ${ id }titles[i-1] + "</p>");

}

function ${ id }next() { 
    var i=${ id }loc+1;
    log_event("seq_next", {'old':${id}loc, 'new':i,'id':'${id}'});
    if(i > ${ len(items) } ) {
      i = ${ len(items) };
  } else {
    ${ id }goto(i);
  };
}


function ${ id }prev() { 
    var i=${ id }loc-1;
    log_event("seq_prev", {'old':${id}loc, 'new':i,'id':'${id}'});
    if (i < 1 ) {
      i = 1;
    } else {
    ${ id }goto(i);
  };
}



$(function() {
  var i; 
  for(i=1; i<${ len(items)+1 }; i++) {
    ${ id }setup_click(i);
  }


  $('.${ id }next a').click(function(eo) { ${ id }next(); return false;});
  $('.${ id }prev a').click(function(eo) { ${ id }prev(); return false;});
  ${ id }goto( ${ position } );

});
