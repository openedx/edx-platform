define(["jquery", "backbone", "underscore"], function($, Backbone) {
    return (function() {
            var cdnLinks_autoComplete_m3u8 = function() {
                $(".wrapper-videolist-url.videolist-settings-item .input.videolist-url").autocomplete({
                    source: function(request, response) {
			            api_url = window.location.hostname.includes("learn-cmu.talentsprint.com") ? "https://cdn-intl.talentsprint.com/findFilePaths" : "https://cdn.exec.talentsprint.com/app/findFilePaths";
                        $.ajax({
                            type: "POST",
                            url: api_url,
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
                       	if(ui.item.domain == "cdn.exec.talentsprint.com" || ui.item.domain == "cdn.chn.talentsprint.com" || ui.item.domain == "cdn-intl.talentsprint.com") {
                            ui.item.value = "https://" + ui.item.domain + "/e_content/" + ui.item.value;
                        }else {
                            ui.item.value = "https://" + ui.item.domain + "/e_content/" + Crypto.MD5(ui.item.value + "dingdong") + "/" + ui.item.value;
                        }
 
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
