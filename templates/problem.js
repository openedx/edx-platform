function ${ id }_load() {
  $('#main_${ id }').load('${ ajax_url }problem_get?id=${ id }', 
  function() {
  MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
  update_schematics();

  $('#check_${ id }').click(function() {
    $("input.schematic").each(function(index,element){ element.schematic.update_value(); });
    var submit_data={};
    $.each($("[id^=input_${ id }_]"), function(index,value){
	    if (value.type==="radio" || value.type==="checkbox"){
		if (value.checked) {
		    if (typeof submit_data[value.name] == 'undefined'){
			submit_data[value.name]=[]
		    }
		    submit_data[value.name]+=value.value;
		}
	    }
	    else{
		submit_data[value.id]=value.value;
	    }
    });
    postJSON('/modx/problem/${ id }/problem_check',
    submit_data,
    function(json) {
      switch(json.success) {
      case 'incorrect': // Worked, but answer not 
      case 'correct':
	  ${ id }_load();
      //alert("!!"+json.success);  
          break;
      default:
        alert(json.success);  
      }
    });
    log_event('problem_check', submit_data);
  });

  $('#reset_${ id }').click(function() {
    var submit_data={};
    $.each($("[id^=input_${ id }_]"), function(index,value){
      submit_data[value.id]=value.value;
    });

    postJSON('/modx/problem/${ id }/problem_reset', {'id':'${ id }'}, function(json) {
      ${ id }_load();
    });
    log_event('problem_reset', submit_data);
  });

  $('#show_${ id }').click(function() {
    postJSON('/modx/problem/${ id }/problem_show', {}, function(data) {
      for (var key in data) {
      $("#answer_"+key).text(data[key]);
    }
  });

  log_event('problem_show', {'problem':'${ id }'});
});

$('#save_${ id }').click(function() {
  $("input.schematic").each(function(index,element){ element.schematic.update_value(); });
  var submit_data={};
  $.each($("[id^=input_${ id }_]"), function(index,value){
    submit_data[value.id]=value.value;});
    postJSON('/modx/problem/${ id }/problem_save',
    submit_data, function(data){
      if(data.success) {
        alert('Saved');
      }}
    );
    log_event('problem_save', submit_data);
  });
}
);}

$(function() {
  ${ id }_load();
});
