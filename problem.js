function ${ id }_load() {
   $('#main_${ id }').load('${ ajax_url }problem_get?id=${ id }', 
      function() {
        MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
	update_schematics();

	$('#check_${ id }').click(function() {
	  var submit_data={};
	  $.each($("[id^=input_${ id }_]"), function(index,value){
		  submit_data[value.id]=value.value;
	      });

	  if($('#check_${ id }').attr('value').substring(0,5) != 'Reset') { 
	      $.getJSON('/modx/problem/${ id }/problem_check',
		submit_data,
		function(json) {
  		  ${ id }_load();
		});
	  } else /* if 'Reset' */ {
	      $.getJSON('/modx/problem/${ id }/problem_reset', {'id':'${ id }'}, function(json) {
		${ id }_load();
		  });
	  }
	    });
	$('#show_${ id }').click(function() {
		$.getJSON('/modx/problem/${ id }/problem_show', function(data) {
			for (var key in data) {
			    $("#answer_${ id }_"+key).text(data[key]);
			}
		    });
	    });
	$('#save_${ id }').click(function() {
	  var submit_data={};
	  $.each($("[id^=input_${ id }_]"), function(index,value){
		  submit_data[value.id]=value.value;});
	      $.getJSON('/modx/problem/${ id }/problem_save',
			submit_data, function(data){
			    if(data.success) {
				alert('Saved');
			    }}
			);
	    });
			   }
			   );}
$(function() {
	${ id }_load();
});
