(function (window, undefined) {
    Transcripts.MessageManager = Backbone.View.extend({
        tagName: 'div',
        elClass: '.wrapper-transcripts-message',
        invisibleClass: 'is-invisible',

        events: {
            'click .setting-import': 'importHandler',
            'click .setting-replace': 'replaceHandler',
            'click .setting-choose': 'chooseHandler',
            'click .setting-use-existing': 'useExistingHandler'
        },

        // Pre-defined dict with anchors to status templates.
        templates: {
            not_found: '#transcripts-not-found',
            found: '#transcripts-found',
            import: '#transcripts-import',
            replace:  '#transcripts-replace',
            uploaded:  '#transcripts-uploaded',
            use_existing: '#transcripts-use-existing',
            choose: '#transcripts-choose'
        },

        initialize: function () {
            _.bindAll(this);

            this.component_id = this.$el.closest('.component').data('id');

            this.fileUploader = new Transcripts.FileUploader({
                el: this.$el,
                messenger: this,
                component_id: this.component_id,
                videoListObject: this.options.parent
            });
        },

        render: function (template_id, params) {
            var tplHtml = $(this.templates[template_id]).text(),
                videoList = this.options.parent.getVideoObjectsList(),
            // Change list representation format to more convenient and group
            // them by video property.
            //                  Before:
            // [
            //      {mode: `html5`, type: `mp4`, video: `video_name_1`},
            //      {mode: `html5`, type: `webm`, video: `video_name_2`}
            // ]
            //                  After:
            // {
            //      `video_name_1`: [{mode: `html5`, type: `webm`, ...}],
            //      `video_name_2`: [{mode: `html5`, type: `mp4`, ...}]
            // }
                groupedList = _.groupBy(
                    videoList,
                    function (value) {
                        return value.video;
                    }
                ),
                html5List = (params) ? params.html5_local : [],
                template;

            if (!tplHtml) {
                console.error('Couldn\'t load Transcripts status template');

                return;
            }

            template = _.template(tplHtml);

            this.$el.find('.transcripts-status')
                .removeClass('is-invisible')
                .find(this.elClass).html(template({
                    component_id: encodeURIComponent(this.component_id),
                    html5_list: html5List,
                    grouped_list: groupedList,
                    subs_id: (params) ? params.subs: ''
                }));

            this.fileUploader.render();

            return this;
        },

        /**
        * @function
        *
        * Shows error message.
        *
        * @param {string} err Error message that will be shown
        *
        * @param {boolean} hideButtons Hide buttons
        *
        */
        showError: function (err, hideButtons) {
            var $error = this.$el.find('.transcripts-error-message');

            if (err) {
                // Hide any other error messages.
                this.hideError();

                $error
                    .html(gettext(err))
                    .removeClass(this.invisibleClass);

                if (hideButtons) {
                    this.$el.find('.wrapper-transcripts-buttons')
                        .addClass(this.invisibleClass);
                }
            }
        },

        /**
        * @function
        *
        * Hides error message.
        *
        */
        hideError: function () {
            this.$el.find('.transcripts-error-message')
                .addClass(this.invisibleClass);

            this.$el.find('.wrapper-transcripts-buttons')
                .removeClass(this.invisibleClass);
        },

        /**
        * @function
        *
        * Handle import button.
        *
        * @params {object} event Event object.
        *
        */
        importHandler: function (event) {
            event.preventDefault();

            this.processCommand('replace', 'Error: Import failed.');
        },

        /**
        * @function
        *
        * Handle replace button.
        *
        * @params {object} event Event object.
        *
        */
        replaceHandler: function (event) {
            event.preventDefault();

            this.processCommand('replace', 'Error: Replacing failed.');
        },

        /**
        * @function
        *
        * Handle choose buttons.
        *
        * @params {object} event Event object.
        *
        */
        chooseHandler: function (event) {
            event.preventDefault();

            var videoId = $(event.currentTarget).data('video-id');

            this.processCommand('choose', 'Error: Choosing failed.', videoId);
        },

        /**
        * @function
        *
        * Handle `use existing` button.
        *
        * @params {object} event Event object.
        *
        */
        useExistingHandler: function (event) {
            event.preventDefault();

            this.processCommand('rename', 'Error: Choosing failed.');
        },

        /**
        * @function
        *
        * Decorator for `command` function in the Transcripts.Utils.
        *
        * @params {string} action Action that will be invoked on server. Is a part
        *                         of url.
        *
        * @params {string} errorMessage Error massage that will be shown if any
        *                               connection error occurs
        *
        * @params {string} videoId Extra parameter that sometimes should be sent
        *                          to the server
        *
        */
        processCommand: function (action, errorMessage, videoId) {
            var self = this,
                utils = Transcripts.Utils,
                component_id = this.component_id,
                videoList = this.options.parent.getVideoObjectsList(),
                extraParam;

            if (videoId) {
                extraParam = { html5_id: videoId };
            }

            utils.command(action, component_id, videoList, extraParam)
                .done(function (resp) {
                    if (resp.status && resp.status === 'Success') {
                        var sub = resp.subs;

                        self.render('found', resp);
                        utils.Storage.set('sub', sub);
                        self.currentItemSubs = sub;
                    } else {
                        self.render('not_found', resp);
                    }
                })
                .fail(function (resp) {
                    self.showError(errorMessage);
                });
        }

    });
}(this));
