(function (define) {

define(
'video/09_poster.js',
['video/00_resizer.js'], function (Resizer) {
    /**
     * VideoPoster module exports a function.
     *
     * @type {function}
     * @access public
     *
     * @param {object} state - The object containing the state of the video
     *     player. All other modules, their parameters, public variables, etc.
     *     are available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {jquery Promise}
     */
    var VideoPoster = function (element, options) {
        if (!(this instanceof VideoPoster)) {
            return new VideoPoster(state);
        }

        _.bindAll(this, 'onClick', 'destroy');
        this.dfd = $.Deferred();
        this.element = element;
        this.container = element.find('.video-player');
        this.options = options || {};
        this.initialize();
    };

    VideoPoster.moduleName = 'Poster';
    VideoPoster.prototype = {
        template: _.template([
            '<div class="poster-<%= type %> poster" ',
                'style="background-image: url(<%= url %>)">',
                '<span tabindex="0" class="btn-play" aria-label="',
                    gettext('Play video'), '"></span>',
            '</div>'
        ].join('')),

        initialize: function () {
            this.el = $(this.template({
                url: this.options.poster.url,
                type: this.options.poster.type
            }));
            this.element.addClass('is-poster');
            this.resizer = new Resizer({
                element: this.container,
                elementRatio: 16/9,
                container: this.element
            }).delta.add(47, 'height').setMode('width');
            this.render();
            this.bindHandlers();
        },

        bindHandlers: function () {
            var self = this;
            this.el.on('click', this.onClick);
            this.element.on('play destroy', this.destroy);
            $(window).on('resize.poster', _.debounce(function () {
                self.resizer.align();
            }, 100));
        },

        render: function () {
            this.container.append(this.el);
        },

        onClick: function () {
            if (_.isFunction(this.options.onClick)) {
                this.options.onClick();
            }
        },

        destroy: function () {
            this.element.off('play destroy', this.destroy);
            $(window).off('resize.poster');
            this.element.removeClass('is-poster');
            this.resizer.destroy();
            this.el.remove();
        }
    };

    return VideoPoster;
});

}(RequireJS.define));
