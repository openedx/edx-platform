
var liveSearch = function(query_string) {
    var query = $('input#keywords');
    var query_val = function () {return $.trim(query.val());};
    var prev_text = query_val();
    var running = false;
    var q_list_sel = 'question-list';//id of question listing div
    var search_url = askbot['urls']['questions'];
    var x_button = $('input[name=reset_query]');

    var refresh_x_button = function(){
        if(query_val().length > 0){
            if (query.hasClass('searchInput')){
                query.attr('class', 'searchInputCancelable');
                x_button.show();
            }
        } else {
            x_button.hide();
            query.attr('class', 'searchInput');
        }
    };

    var restart_query = function() {
        sortMethod = 'activity-desc';
        query.val('');
        refresh_x_button();
        send_query();
    };

    var eval_query = function(){
        cur_query = query_val();
        if (cur_query !== prev_text && running === false){
            if (cur_query.length >= minSearchWordLength){
                send_query(cur_query);
            } else if (cur_query.length === 0){
                restart_query();
            }
        }
    };

    var update_query_string = function(query_text){
        if(query_text === undefined) { // handle missing parameter
            query_text = query_val();
        }
        query_string = QSutils.patch_query_string(
                query_string,
                'query:' + encodeURIComponent(query_text),
                query_text === ''   // remove if empty
        );
        return query_text;
    };

    var send_query = function(query_text){
        running = true;
        if(!prev_text && query_text && showSortByRelevance) {
            // If there was no query but there is some query now - and we support relevance search - then switch to it */
            query_string = QSutils.patch_query_string(query_string, 'sort:relevance-desc');
        }
        prev_text = update_query_string(query_text);
        query_string = QSutils.patch_query_string(query_string, 'page:1'); /* if something has changed, then reset the page no. */
        var url = search_url + query_string;
        $.ajax({
            url: url,
            dataType: 'json',
            success: render_result,
            complete: function(){
                running = false;
                eval_query();
            },
            cache: false
        });
        var context = { state:1, rand:Math.random() };
        History.pushState( context, "Questions", url );
        setTimeout(function (){
            /* HACK: For some weird reson, sometimes something overrides the above pushState so we re-aplly it
                     This might be caused by some other JS plugin.
                     The delay of 10msec allows the other plugin to override the URL.
            */
            History.replaceState( context, "Questions", url );
        }, 10);
    };

    /* *********************************** */

    var render_related_tags = function(tags, query_string){
        if (tags.length === 0) return;

        var html_list = [];
        for (var i=0; i<tags.length; i++){
            var tag = new Tag();
            tag.setName(tags[i]['name']);
            tag.setDeletable(false);
            tag.setLinkable(true);
            tag.setUrlParams(query_string);

            html_list.push(tag.getElement().outerHTML());
            html_list.push('<span class="tag-number">');
            html_list.push(tags[i]['used_count']);
            html_list.push('</span>');
        }
        $('#related-tags').html(html_list.join(''));
    };

    var render_search_tags = function(tags, query_string){
        var search_tags = $('#searchTags');
        search_tags.empty();
        if (tags.length === 0){
            $('#listSearchTags').hide();
            $('#search-tips').hide();//wrong - if there are search users
        } else {
            $('#listSearchTags').show();
            $('#search-tips').show();
            $.each(tags, function(idx, tag_name){
                var tag = new Tag();
                tag.setName(tag_name);
                tag.setLinkable(false);
                tag.setDeletable(true);
                tag.setDeleteHandler(
                    function(){
                        remove_search_tag(tag_name, query_string);
                    }
                );
                search_tags.append(tag.getElement());
            });
        }
    };

    var create_relevance_tab = function(query_string){
        relevance_tab = $('<a></a>');
        href = search_url + QSutils.patch_query_string(query_string, 'sort:relevance-desc');
        relevance_tab.attr('href', href);
        relevance_tab.attr('id', 'by_relevance');
        relevance_tab.html('<span>' + sortButtonData['relevance']['label'] + '</span>');
        return relevance_tab;
    };

    /* *************************************** */

    var remove_search_tag = function(tag){
        query_string = QSutils.remove_search_tag(query_string, tag);
        send_query();
    };

    var set_active_sort_tab = function(sort_method, query_string){
        var tabs = $('#sort_tabs > a');
        tabs.attr('class', 'off');
        tabs.each(function(index, element){
            var tab = $(element);
            var tab_name = tab.attr('id').replace(/^by_/,'');
            if (tab_name in sortButtonData){
                href = search_url + QSutils.patch_query_string(query_string, 'sort:'+tab_name+'-desc');
                tab.attr('href', href);
                tab.attr('title', sortButtonData[tab_name]['desc_tooltip']);
                tab.html(sortButtonData[tab_name]['label']);
            }
        });
        var bits = sort_method.split('-', 2);
        var name = bits[0];
        var sense = bits[1];//sense of sort
        var antisense = (sense == 'asc' ? 'desc':'asc');
        var arrow = (sense == 'asc' ? ' &#9650;':' &#9660;');
        var active_tab = $('#by_' + name);
        active_tab.attr('class', 'on');
        active_tab.attr('title', sortButtonData[name][antisense + '_tooltip']);
        active_tab.html(sortButtonData[name]['label'] + arrow);
    };

    var render_relevance_sort_tab = function(query_string){
        if (showSortByRelevance === false){
            return;
        }
        var relevance_tab = $('#by_relevance');
        if (prev_text && prev_text.length > 0){
            if (relevance_tab.length == 0){
                relevance_tab = create_relevance_tab(query_string);
                $('#sort_tabs>span').after(relevance_tab);
            }
        }
        else {
            if (relevance_tab.length > 0){
                relevance_tab.remove();
            }
        }
    };

    var render_result = function(data, text_status, xhr){
        if (data['questions'].length > 0){
            $('#pager').toggle(data['paginator'] !== '').html(data['paginator']);
            $('#questionCount').html(data['question_counter']);
            render_search_tags(data['query_data']['tags'], data['query_string']);
            if(data['faces'].length > 0) {
                $('#contrib-users > a').remove();
                $('#contrib-users').append(data['faces'].join(''));
            }
            render_related_tags(data['related_tags'], data['query_string']);
            render_relevance_sort_tab(data['query_string']);
            set_active_sort_tab(data['query_data']['sort_order'], data['query_string']);
            if(data['feed_url']){
                // Change RSS URL
                $("#ContentLeft a.rss:first").attr("href", data['feed_url']);
            }

            // Patch scope selectors
            $('#scopeWrapper > a.scope-selector').each(function(index) {
                var old_qs = $(this).attr('href').replace(search_url, '');
                var scope = QSutils.get_query_string_selector_value(old_qs, 'scope');
                qs = QSutils.patch_query_string(data['query_string'], 'scope:' + scope);
                $(this).attr('href', search_url + qs);
            });

            // Patch "Ask your question"
            // var askButton = $('#askButton');
            // var askHrefBase = askButton.attr('href').split('?')[0];
            // askButton.attr('href', askHrefBase + data['query_data']['ask_query_string']); /* INFO: ask_query_string should already be URL-encoded! */


            query.focus();

            var old_list = $('#' + q_list_sel);
            var new_list = $('<div></div>').hide().html(data['questions']);
            old_list.stop(true).after(new_list).fadeOut(200, function() {
                //show new div with a fadeIn effect
                old_list.remove();
                new_list.attr('id', q_list_sel);
                new_list.fadeIn(400);            
            });
        }
    };

    /* *********************************** */

    // Wire search tags
    var search_tags = $('#searchTags .tag-left');
    $.each(search_tags, function(idx, element){
        var tag = new Tag();
        tag.decorate($(element));
        //todo: setDeleteHandler and setHandler
        //must work after decorate & must have getName
        tag.setDeleteHandler(
                function(){
                    remove_search_tag(tag.getName(), query_string);
                }
        );
    });

    // Wire X button
    x_button.click(function () {
        restart_query(); /* wrapped in closure because it's not yet defined at this point */
    });
    refresh_x_button();

    // Wire query box
    var main_page_eval_handle;
    query.keyup(function(e){
        refresh_x_button();
        if (running === false){
            clearTimeout(main_page_eval_handle);
            main_page_eval_handle = setTimeout(eval_query, 400);
        }
    });

    $("form#searchForm").submit(function(event) {
        // if user clicks the button the s(h)e probably wants page reload,
        // so provide that experience but first update the query string
        event.preventDefault();
        update_query_string();
        window.location.href = search_url + query_string;
    });

    /* *********************************** */

    // Hook for tag_selector.js
    liveSearch.refresh = function () {
        send_query();
    };
};
