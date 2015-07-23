define([
    'jquery'
    ], function($) {

    /*
     * Select menu replacement
     * Handles functionality for the replacement select menus, which
     * allows us to style them to our liking. Accessibility is main-
     * tained via use of the default select control. The replacement 
     * control is not visible to screen readers.
     *
     * Choosing an option in the replacement menu also updates the
     * default select menu thus maintaining accessibility.
     */


    var CustomSelectReplacement = {

        vars: {
            replaced:       $('.replace-select'),
            replacedClass:  'is-replaced is-transparent',
            customClass:    'wrapper-custom-select',
            wrapperClass:   'wrapper-replace-select',
            valueClass:     'replace-value',
            iconClass:      'icon-caret-down',
            hoverClass:     'is-hover'
        },

        init: function() {
            this.replaceFoundSelects();
            this.listenForSelectClick();
            this.listenForSelectEvents();
        },

        replaceFoundSelects: function() {
            var variables = this.vars;

            if (variables.replaced.length) {

                variables.replaced.each(function(index, el) {
                    var $el = $(el),
                        replaced = $el.clone(),
                        statuses = [];

                    if ($el.hasClass('has-success')) {
                        statuses.push('has-success');
                    }

                    if ($el.hasClass('has-error')) {
                        statuses.push('has-error');
                    }

                    if ($el.is(':disabled')) {
                        statuses.push('is-disabled');
                    }

                    $el.addClass(variables.replacedClass);

                    $el.replaceWith([
                        '<div class="' + variables.wrapperClass + '">',
                            '<select class="' + replaced[0].className + ' is-replaced" id="' + replaced[0].id + '" name="' + replaced[0].name + '" ' + replaced[0].attributes[0].name + '>' + replaced[0].innerHTML + '</select>',
                            '<span class="' + variables.customClass + ' ' + statuses.join(' ') + '" aria-hidden="true">',
                                '<span class="' + variables.valueClass + '">' + CustomSelectReplacement.setInitialText($el) + '</span>',
                                '<svg class="icon ' + variables.iconClass + '" title="Down arrow">',
                                    '<use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/public/images/edx-svg/svgdefs.svg#' + variables.iconClass + '"></use>',
                                '</svg>',
                            '</span>',
                        '</div>'
                        ].join(''));
                });
            }
        },

        setInitialText: function(el) {
            return el.find('option:first').text()
        },

        listenForSelectClick: function() {
            $('.field').on('change', this.vars.replaced, function(event) {
                CustomSelectReplacement.updateReplacedOption($(event.target));
            });
        },

        updateReplacedOption: function(el) {
            var val = el.val(),
                wrapper = el.parent('.' + this.vars.wrapperClass),
                text = wrapper.find('.' + this.vars.valueClass);

            text.text(val);
        },

        listenForSelectEvents: function() {
            var variables = this.vars;

            variables.replaced.on('hover mouseover mouseenter', function(event) {
                var $el = $(event.target);

                $el.next(variables.customWrapper)
                    .addClass(variables.hoverClass);
            }).on('blur mouseout mouseleave', function(event) {
                var $el = $(event.target);

                $el.next(variables.customWrapper)
                    .removeClass(variables.hoverClass);
            });
        }

    };

    CustomSelectReplacement.init();
});