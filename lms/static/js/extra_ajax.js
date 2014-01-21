  $(function(){
      $("#city").autocomplete({
        source: function(request, response){
            $.ajax({
                url: "/city_lookup/",
                dataType: "json",
                data: {
                    query: request.term,
                },
                success: function(data){
                    response( $.map(data, function(item){
                      $("#city_id").val(item[0]); 
                      return {
                          label: item[1],
                          value: item[1]
                      }
                    }));
                }
            });
        },
        open: function(){
            $(this).removeClass("ui-corner-all").addClass("ui-corner-top");
        },
        close: function(){
            $(this).removeClass("ui-corner-top").addClass("ui-corner-all");
        }
      })
  });

$(function(){
    $("#cedula").bind("change keyup",function(){
        var cedula = $("input#cedula").val();
        if (cedula.length!=10){
            return
        }
        $.ajax({
            url: "/user_lookup/",
            dataType: "json",
            minLength: 10,
            data: {
                query: cedula
            },
            success: function(data){
                if (data){
                    $("#number_senescyt").val(data['number_senescyt']); 
                    return;
                }
            }
        });
    })
  });
