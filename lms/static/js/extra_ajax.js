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
        var senescyt = $("#number_senescyt");
        var name = $("#name");
        if (cedula.length!=10){
            senescyt.val("");
            name.val("");
            return
        }
        $.ajax({
            url: "/user_lookup/",
            dataType: "json",
            minLength: 10,
            data: {
                cedula: cedula
            },
            success: function(data){
                if (data['result']==true){
                    senescyt.val(data['number_senescyt']); 
                    name.val(data['nombre']);
                    return;
                }else{
                    senescyt.val("Ninguno");
                }
            }
        });
    })
  });
