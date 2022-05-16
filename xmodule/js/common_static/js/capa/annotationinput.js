(function() {
    var debug = false;

    var module = {
        debug: debug,
        inputSelector: '.annotation-input',
        tagSelector: '.tag',
        tagsSelector: '.tags',
        commentSelector: 'textarea.comment',
        valueSelector: 'input.value', // stash tag selections and comment here as a JSON string...

        singleSelect: true,

        init: function() {
            var that = this;

            if (this.debug) { console.log('annotation input loaded: '); }

            $(this.inputSelector).each(function(index, el) {
                if (!$(el).data('listening')) {
                    $(el).delegate(that.tagSelector, 'click', $.proxy(that.onClickTag, that));
                    $(el).delegate(that.commentSelector, 'change', $.proxy(that.onChangeComment, that));
                    $(el).data('listening', 'yes');
                }
            });
        },
        onChangeComment: function(e) {
            var value_el = this.findValueEl(e.target);
            var current_value = this.loadValue(value_el);
            var target_value = $(e.target).val();

            current_value.comment = target_value;
            this.storeValue(value_el, current_value);
        },
        onClickTag: function(e) {
            var target_el = e.target,
                target_value, target_index;
            var value_el, current_value;

            value_el = this.findValueEl(e.target);
            current_value = this.loadValue(value_el);
            target_value = $(e.target).data('id');

            if (!$(target_el).hasClass('selected')) {
                if (this.singleSelect) {
                    current_value.options = [target_value];
                } else {
                    current_value.options.push(target_value);
                }
            } else {
                if (this.singleSelect) {
                    current_value.options = [];
                } else {
                    target_index = current_value.options.indexOf(target_value);
                    if (target_index !== -1) {
                        current_value.options.splice(target_index, 1);
                    }
                }
            }

            this.storeValue(value_el, current_value);

            if (this.singleSelect) {
                $(target_el).closest(this.tagsSelector)
                    .find(this.tagSelector)
                    .not(target_el)
                    .removeClass('selected');
            }
            $(target_el).toggleClass('selected');
        },
        findValueEl: function(target_el) {
            var input_el = $(target_el).closest(this.inputSelector);
            return $(this.valueSelector, input_el);
        },
        loadValue: function(value_el) {
            var json = $(value_el).val();

            var result = JSON.parse(json);
            if (result === null) {
                result = {};
            }
            if (!result.hasOwnProperty('options')) {
                result.options = [];
            }
            if (!result.hasOwnProperty('comment')) {
                result.comment = '';
            }

            return result;
        },
        storeValue: function(value_el, new_value) {
            var json = JSON.stringify(new_value);
            $(value_el).val(json);
        }
    };

    module.init();
}).call(this);
