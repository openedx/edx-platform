(function() {
    // eslint-disable-next-line no-var
    var debug = false;

    // eslint-disable-next-line no-var
    var module = {
        debug: debug,
        inputSelector: '.annotation-input',
        tagSelector: '.tag',
        tagsSelector: '.tags',
        commentSelector: 'textarea.comment',
        valueSelector: 'input.value', // stash tag selections and comment here as a JSON string...

        singleSelect: true,

        init: function() {
            // eslint-disable-next-line no-var
            var that = this;

            // eslint-disable-next-line no-console
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
            /* eslint-disable-next-line camelcase, no-var */
            var value_el = this.findValueEl(e.target);
            /* eslint-disable-next-line camelcase, no-var */
            var current_value = this.loadValue(value_el);
            /* eslint-disable-next-line camelcase, no-var */
            var target_value = $(e.target).val();

            // eslint-disable-next-line camelcase
            current_value.comment = target_value;
            this.storeValue(value_el, current_value);
        },
        onClickTag: function(e) {
            /* eslint-disable-next-line camelcase, no-var */
            var target_el = e.target,
                // eslint-disable-next-line camelcase
                target_value, target_index;
            /* eslint-disable-next-line camelcase, no-var */
            var value_el, current_value;

            // eslint-disable-next-line camelcase
            value_el = this.findValueEl(e.target);
            // eslint-disable-next-line camelcase
            current_value = this.loadValue(value_el);
            // eslint-disable-next-line camelcase
            target_value = $(e.target).data('id');

            if (!$(target_el).hasClass('selected')) {
                if (this.singleSelect) {
                    // eslint-disable-next-line camelcase
                    current_value.options = [target_value];
                } else {
                    // eslint-disable-next-line camelcase
                    current_value.options.push(target_value);
                }
            } else {
                if (this.singleSelect) {
                    // eslint-disable-next-line camelcase
                    current_value.options = [];
                } else {
                    // eslint-disable-next-line camelcase
                    target_index = current_value.options.indexOf(target_value);
                    // eslint-disable-next-line camelcase
                    if (target_index !== -1) {
                        // eslint-disable-next-line camelcase
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
        // eslint-disable-next-line camelcase
        findValueEl: function(target_el) {
            /* eslint-disable-next-line camelcase, no-var */
            var input_el = $(target_el).closest(this.inputSelector);
            return $(this.valueSelector, input_el);
        },
        // eslint-disable-next-line camelcase
        loadValue: function(value_el) {
            // eslint-disable-next-line no-var
            var json = $(value_el).val();

            // eslint-disable-next-line no-var
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
        // eslint-disable-next-line camelcase
        storeValue: function(value_el, new_value) {
            // eslint-disable-next-line no-var
            var json = JSON.stringify(new_value);
            $(value_el).val(json);
        }
    };

    module.init();
}).call(this);
