define(
    [
        'jquery', 'backbone', 'underscore',
        'js/views/video/transcripts/utils', 'js/views/video/transcripts/file_uploader',
        'gettext'
    ],
    function($, Backbone, _, Utils, FileUploader, gettext) {
        var MessageManager = Backbone.View.extend({
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
                replace: '#transcripts-replace',
                uploaded: '#transcripts-uploaded',
                use_existing: '#transcripts-use-existing',
                choose: '#transcripts-choose'
            },

            initialize: function(options) {
                _.bindAll(this,
                    'importHandler', 'replaceHandler', 'chooseHandler', 'useExistingHandler', 'showError', 'hideError'
                );

                this.options = _.extend({}, options);

                this.component_locator = this.$el.closest('[data-locator]').data('locator');

                this.fileUploader = new FileUploader({
                    el: this.$el,
                    messenger: this,
                    component_locator: this.component_locator
                });
            },

            render: function(template_id, params) {
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
                        function(value) {
                            return value.video;
                        }
                    ),
                    html5List = (params) ? params.html5_local : [],
                    template;

                if (!tplHtml) {
                    console.error('Couldn\'t load Transcripts status template');

                    return this;
                }

                template = edx.HtmlUtils.template(tplHtml);

                edx.HtmlUtils.setHtml(
                    this.$el.find('.transcripts-status').removeClass('is-invisible').find(this.elClass), template({
                        component_locator: encodeURIComponent(this.component_locator),
                        html5_list: html5List,
                        grouped_list: groupedList,
                        subs_id: (params) ? params.subs : ''
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
            showError: function(err, hideButtons) {
                var $error = this.$el.find('.transcripts-error-message');

                if (err) {
                // Hide any other error messages.
                    this.hideError();
                    edx.HtmlUtils.setHtml($error, gettext(err)).removeClass(this.invisibleClass);
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
            hideError: function() {
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
            importHandler: function(event) {
                event.preventDefault();

                this.processCommand('replace', gettext('Error: Import failed.'));
            },

            /**
        * @function
        *
        * Handle replace button.
        *
        * @params {object} event Event object.
        *
        */
            replaceHandler: function(event) {
                event.preventDefault();

                this.processCommand('replace', gettext('Error: Replacing failed.'));
            },

            /**
        * @function
        *
        * Handle choose buttons.
        *
        * @params {object} event Event object.
        *
        */
            chooseHandler: function(event) {
                event.preventDefault();

                var videoId = $(event.currentTarget).data('video-id');

                this.processCommand('choose', gettext('Error: Choosing failed.'), videoId);
            },

            /**
        * @function
        *
        * Handle `use existing` button.
        *
        * @params {object} event Event object.
        *
        */
            useExistingHandler: function(event) {
                event.preventDefault();

                this.processCommand('rename', gettext('Error: Choosing failed.'));
            },

            /**
        * @function
        *
        * Decorator for `command` function in the Utils.
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
            processCommand: function(action, errorMessage, videoId) {
                var self = this,
                    component_locator = this.component_locator,
                    videoList = this.options.parent.getVideoObjectsList(),
                    extraParam, xhr;

                if (videoId) {
                    extraParam = {html5_id: videoId};
                }

                xhr = Utils.command(action, component_locator, videoList, extraParam)
                    .done(function(resp) {
                        var edxVideoID = resp.edx_video_id;

                        self.render('found', resp);
                        Backbone.trigger('transcripts:basicTabUpdateEdxVideoId', edxVideoID);
                    })
                    .fail(function(resp) {
                        var message = resp.status || errorMessage;
                        self.showError(message);
                    });

                return xhr;
            }

        });

        return MessageManager;
    });
