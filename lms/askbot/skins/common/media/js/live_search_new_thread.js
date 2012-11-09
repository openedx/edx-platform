
var liveSearchNewThreadInit = function() {
    var query = $('input#id_title.questionTitleInput');
    var prev_text = $.trim(query.val());
    var search_url = askbot['urls']['api_get_questions'];
    var running = false;
    var q_list_sel = 'question-list'; //id of question listing div

    running = false;
    var ask_page_eval_handle;
    query.keyup(function(e){
        if (running === false){
            clearTimeout(ask_page_eval_handle);
            ask_page_eval_handle = setTimeout(eval_query, 400);
        }
    });

    var eval_query = function(){
        cur_text = $.trim(query.val());
        if (cur_text !== prev_text && running === false){
            if (cur_text.length >= minSearchWordLength){
                send_query(cur_text);
            } else if (cur_text.length === 0){
                /* restart query */
                $('#' + q_list_sel).css('height',0).children().remove();
                running = false;
                prev_text = '';
            }
        }
    };

    var render_result = function(data, text_status, xhr){
        var container = $('#' + q_list_sel);
        container.fadeOut(200, function() {
            container.children().remove();
            $.each(data, function(idx, question){
                var url = question['url'];
                var title = question['title'];
                var answer_count = question['answer_count'];
                var list_item = $('<h2></h2>');
                var count_element = $('<span class="item-count"></span>');
                count_element.html(answer_count);
                list_item.append(count_element);
                var link = $('<a></a>');
                link.attr('href', url);
                list_item.append(link);
                title_element = $('<span class="title"></span>');
                title_element.html(title);
                link.append(title)
                container.append(list_item);
            });
            container.show();//show just to measure
            var unit_height = container.children(':first').outerHeight();
            container.hide();//now hide
            if (data.length > 5){
                container.css('overflow-y', 'scroll');
                container.css('height', unit_height*6 + 'px');
            } else {
                container.css('height', data.length*unit_height + 'px');
                container.css('overflow-y', 'hidden');
            }
            container.fadeIn();
        });
    };

    var send_query = function(query_text){
        prev_text = query_text;
        running = true;
        $.ajax({
            url: search_url,
            dataType: 'json',
            success: render_result,
            complete: function() {
                running = false;
                eval_query();
            },
            data: {query: query_text},
            cache: false
        });
    }

};
