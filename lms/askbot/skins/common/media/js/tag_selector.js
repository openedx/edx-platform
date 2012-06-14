
var TagDetailBox = function(box_type){
    WrappedElement.call(this);
    this.box_type = box_type;
    this._is_blank = true;
    this._tags = new Array();
    this.wildcard = undefined;
};
inherits(TagDetailBox, WrappedElement);

TagDetailBox.prototype.createDom = function(){
    this._element = this.makeElement('div');
    this._element.addClass('wildcard-tags');
    this._headline = this.makeElement('p');
    this._headline.html(gettext('Tag "<span></span>" matches:'));
    this._element.append(this._headline);
    this._tag_list_element = this.makeElement('ul');
    this._tag_list_element.addClass('tags');
    this._element.append(this._tag_list_element);
    this._footer = this.makeElement('p');
    this._footer.css('clear', 'left');
    this._element.append(this._footer);
    this._element.hide();
};

TagDetailBox.prototype.belongsTo = function(wildcard){
    return (this.wildcard === wildcard);
};

TagDetailBox.prototype.isBlank = function(){
    return this._is_blank;
};

TagDetailBox.prototype.clear = function(){
    if (this.isBlank()){
        return;
    }
    this._is_blank = true;
    this.getElement().hide();
    this.wildcard = null;
    $.each(this._tags, function(idx, item){
        item.dispose();
    });
    this._tags = new Array();
};

TagDetailBox.prototype.loadTags = function(wildcard, callback){
    var me = this;
    $.ajax({
        type: 'GET',
        dataType: 'json',
        cache: false,
        url: askbot['urls']['get_tags_by_wildcard'],
        data: { wildcard: wildcard },
        success: callback,
        failure: function(){ me._loading = false; }
    });
};

TagDetailBox.prototype.renderFor = function(wildcard){
    var me = this;
    if (this._loading === true){
        return;
    }
    this._loading = true;
    this.loadTags(
        wildcard,
        function(data, text_status, xhr){
            me._tag_names = data['tag_names'];
            if (data['tag_count'] > 0){
                var wildcard_display = wildcard.replace(/\*$/, '&#10045;');
                me._headline.find('span').html(wildcard_display);
                $.each(me._tag_names, function(idx, name){
                    var tag = new Tag();
                    tag.setName(name);
                    //tag.setLinkable(false);
                    me._tags.push(tag);
                    me._tag_list_element.append(tag.getElement());
                });
                me._is_blank = false;
                me.wildcard = wildcard;
                var tag_count = data['tag_count'];
                if (tag_count > 20){
                    var fmts = gettext('and %s more, not shown...');
                    var footer_text = interpolate(fmts, [tag_count - 20]);
                    me._footer.html(footer_text);
                    me._footer.show();
                } else {
                    me._footer.hide();
                }
                me._element.show();
            } else {
                me.clear();
            }
            me._loading = false;
        }
    );
}

function pickedTags(){
    
    var interestingTags = {};
    var ignoredTags = {};
    var interestingTagDetailBox = new TagDetailBox('interesting');
    var ignoredTagDetailBox = new TagDetailBox('ignored');

    var sendAjax = function(tagnames, reason, action, callback){
        var url = '';
        if (action == 'add'){
            if (reason == 'good'){
                url = askbot['urls']['mark_interesting_tag'];
            }
            else {
                url = askbot['urls']['mark_ignored_tag'];
            }
        }
        else {
            url = askbot['urls']['unmark_tag'];
        }

        var call_settings = {
            type:'POST',
            url:url,
            data: JSON.stringify({tagnames: tagnames}),
            dataType: 'json'
        };
        if (callback !== false){
            call_settings.success = callback;
        }
        $.ajax(call_settings);
    };

    var unpickTag = function(from_target, tagname, reason, send_ajax){
        //send ajax request to delete tag
        var deleteTagLocally = function(){
            from_target[tagname].remove();
            delete from_target[tagname];
        };
        if (send_ajax){
            sendAjax(
                [tagname],
                reason,
                'remove',
                function(){
                    deleteTagLocally();
                    liveSearch.refresh();
                }
            );
        }
        else {
            deleteTagLocally();
        }
    };

    var getTagList = function(reason){
        var base_selector = '.marked-tags';
        if (reason === 'good'){
            var extra_selector = '.interesting';
        } else {
            var extra_selector = '.ignored';
        }
        return $(base_selector + extra_selector);
    };

    var getWildcardTagDetailBox = function(reason){
        if (reason === 'good'){
            return interestingTagDetailBox;
        } else {
            return ignoredTagDetailBox;
        }
    };

    var handleWildcardTagClick = function(tag_name, reason){
        var detail_box = getWildcardTagDetailBox(reason);
        var tag_box = getTagList(reason);
        if (detail_box.isBlank()){
            detail_box.renderFor(tag_name);
        } else if (detail_box.belongsTo(tag_name)){
            detail_box.clear();//toggle off
        } else {
            detail_box.clear();//redraw with new data
            detail_box.renderFor(tag_name);
        }
        if (!detail_box.inDocument()){
            tag_box.after(detail_box.getElement());
            detail_box.enterDocument();
        }
    };

    var renderNewTags = function(
                        clean_tag_names,
                        reason,
                        to_target,
                        to_tag_container
                    ){
        $.each(clean_tag_names, function(idx, tag_name){
            var tag = new Tag();
            tag.setName(tag_name);
            tag.setDeletable(true);

            if (/\*$/.test(tag_name)){
                tag.setLinkable(false);
                var detail_box = getWildcardTagDetailBox(reason);
                tag.setHandler(function(){
                    handleWildcardTagClick(tag_name, reason);
                    if (detail_box.belongsTo(tag_name)){
                        detail_box.clear();
                    }
                });
                var delete_handler = function(){
                    unpickTag(to_target, tag_name, reason, true);
                    if (detail_box.belongsTo(tag_name)){
                        detail_box.clear();
                    }
                }
            } else {
                var delete_handler = function(){
                    unpickTag(to_target, tag_name, reason, true);
                }
            }
            
            tag.setDeleteHandler(delete_handler);
            var tag_element = tag.getElement();
            to_tag_container.append(tag_element);
            to_target[tag_name] = tag_element;
        });
    };

    var handlePickedTag = function(reason){
        var to_target = interestingTags;
        var from_target = ignoredTags;
        var to_tag_container;
        if (reason == 'bad'){
            var input_sel = '#ignoredTagInput';
            to_target = ignoredTags;
            from_target = interestingTags;
            to_tag_container = $('div .tags.ignored');
        }
        else if (reason == 'good'){
            var input_sel = '#interestingTagInput';
            to_tag_container = $('div .tags.interesting');
        }
        else {
            return;
        }

        var tagnames = getUniqueWords($(input_sel).attr('value'));

        $.each(tagnames, function(idx, tagname){
            if (tagname in from_target){
                unpickTag(from_target,tagname,reason,false);
            }
        });

        var clean_tagnames = [];
        $.each(tagnames, function(idx, tagname){
            if (!(tagname in to_target)){
                clean_tagnames.push(tagname);
            }
        });

        if (clean_tagnames.length > 0){
            //send ajax request to pick this tag

            sendAjax(
                clean_tagnames,
                reason,
                'add',
                function(){ 
                    renderNewTags(
                        clean_tagnames,
                        reason,
                        to_target,
                        to_tag_container
                    );
                    $(input_sel).val('');
                    liveSearch.refresh();
                }
            );
        }
    };

    var collectPickedTags = function(section){
        if (section === 'interesting'){
            var reason = 'good';
            var tag_store = interestingTags;
        }
        else if (section === 'ignored'){
            var reason = 'bad';
            var tag_store = ignoredTags;
        }
        else {
            return;
        }
        $('.' + section + '.tags.marked-tags .tag-left').each(
            function(i,item){
                var tag = new Tag();
                tag.decorate($(item));
                tag.setDeleteHandler(function(){
                    unpickTag(
                        tag_store,
                        tag.getName(),
                        reason,
                        true
                    )
                });
                if (tag.isWildcard()){
                    tag.setHandler(function(){
                        handleWildcardTagClick(tag.getName(), reason)
                    });
                }
                tag_store[tag.getName()] = $(item);
            }
        );
    };

    var setupTagFilterControl = function(control_type){
        $('#' + control_type + 'TagFilterControl input')
        .unbind('click')
        .click(function(){
            $.ajax({
                type: 'POST',
                dataType: 'json',
                cache: false,
                url: askbot['urls']['set_tag_filter_strategy'],
                data: {
                    filter_type: control_type,
                    filter_value: $(this).val()
                },
                success: function(){
                    liveSearch.refresh();
                }
            });
        });
    };

    var getResultCallback = function(reason){
        return function(){ 
            handlePickedTag(reason);
        };
    };

    return {
        init: function(){
            collectPickedTags('interesting');
            collectPickedTags('ignored');
            setupTagFilterControl('display');
            var ac = new AutoCompleter({
                url: askbot['urls']['get_tag_list'],
                preloadData: true,
                minChars: 1,
                useCache: true,
                matchInside: true,
                maxCacheLength: 100,
                delay: 10
            });


            var interestingTagAc = $.extend(true, {}, ac);
            interestingTagAc.decorate($('#interestingTagInput'));
            interestingTagAc.setOption('onItemSelect', getResultCallback('good'));

            var ignoredTagAc = $.extend(true, {}, ac);
            ignoredTagAc.decorate($('#ignoredTagInput'));
            ignoredTagAc.setOption('onItemSelect', getResultCallback('bad'));

            $("#interestingTagAdd").click(getResultCallback('good'));
            $("#ignoredTagAdd").click(getResultCallback('bad'));
        }
    };
}

$(document).ready( function(){
    pickedTags().init();
});
