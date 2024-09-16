define(["jquery", "backbone", "underscore"], function($, Backbone) {
    return (function() {
            var cdnLinks_autoComplete_m3u8 = function() {
                $(".wrapper-videolist-url.videolist-settings-item .input.videolist-url").autocomplete({
                    source: function(request, response) {
                        $.ajax({
                            type: "POST",
                            url: "https://cdn.exec.talentsprint.com/app/findFilePaths",
                            dataType: "json",
                            contentType: "application/json; charset=utf-8",
                            data: JSON.stringify({
                                filename: request.term,
                                file_ext: "m3u8",
                                course_id: window.course_location_analytics
                            }),
                            success: function(data) {
                                response($.map(data.filepaths, function (value) {
                                                  return {
                                                            domain: data.domain,
                                                            value: value
                                                  };
                                    })); 
                            },
                        });
                    },
                    minLength: 2,
                    scroll: true,
                    autoFocus: true,
                    select: function(event, ui) {
                        ui.item.value = "https://" + ui.item.domain + "/e_content/" + ui.item.value;
                        $(this).val(ui.item.value);
                        $(this).trigger("input");
                        event.preventDefault();
                    }
                });
            };

        return {
            cdn_m3u8: cdnLinks_autoComplete_m3u8
        };
    }());
});