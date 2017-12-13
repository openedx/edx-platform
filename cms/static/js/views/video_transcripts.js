define(
    ['underscore', 'gettext', 'js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils', 'text!templates/video-transcripts.underscore'],
    function(_, gettext, BaseView, HtmlUtils, StringUtils, videoTranscriptsTemplate) {
        'use strict';

        var VideoTranscriptsView = BaseView.extend({
            tagName: 'div',

            events: {
                'click .toggle-show-transcripts-button': 'toggleShowTranscripts'
            },

            initialize: function(options) {
                this.transcripts = options.transcripts;
                this.edxVideoID = options.edxVideoID;
                this.clientVideoID = options.clientVideoID;
                this.transcriptAvailableLanguages = options.transcriptAvailableLanguages;
                this.videoSupportedFileFormats = options.videoSupportedFileFormats;
                this.videoTranscriptSettings = options.videoTranscriptSettings;
                this.template = HtmlUtils.template(videoTranscriptsTemplate);
            },

            /*
            Sorts object by value and returns a sorted array.
            */
            sortByValue: function(itemObject) {
                var sortedArray = [];
                _.each(itemObject, function(value, key) {
                    // Push each JSON Object entry in array by [value, key]
                    sortedArray.push([value, key]);
                });
                return sortedArray.sort();
            },

            /*
            Returns transcript title.
            */
            getTranscriptClientTitle: function() {
                var clientTitle = this.clientVideoID;
                // Remove video file extension for transcript title.
                _.each(this.videoSupportedFileFormats, function(videoFormat) {
                    clientTitle.replace(videoFormat, '');
                });
                return clientTitle.substring(0, 20);
            },

            /*
            Toggles Show/Hide transcript button and transcripts container.
            */
            toggleShowTranscripts: function() {
                var $transcriptsWrapperEl = this.$el.find('.show-video-transcripts-wrapper');

                // Toggle show transcript wrapper.
                $transcriptsWrapperEl.toggleClass('hidden');

                // Toggle button text.
                HtmlUtils.setHtml(
                    this.$el.find('.toggle-show-transcripts-button-text'),
                    StringUtils.interpolate(
                        gettext('{toggleShowTranscriptText} transcripts ({totalTranscripts})'),
                        {
                            toggleShowTranscriptText: $transcriptsWrapperEl.hasClass('hidden') ? gettext('Show') : gettext('Hide'), // eslint-disable-line max-len
                            totalTranscripts: _.size(this.transcripts)
                        }
                    )
                );

                // Toggle icon class.
                if ($transcriptsWrapperEl.hasClass('hidden')) {
                    this.$el.find('.toggle-show-transcripts-icon').removeClass('fa-caret-down').addClass('fa-caret-right'); // eslint-disable-line max-len
                } else {
                    this.$el.find('.toggle-show-transcripts-icon').removeClass('fa-caret-right').addClass('fa-caret-down'); // eslint-disable-line max-len
                }
            },

            /*
            Renders transcripts view.
            */
            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        transcripts: this.transcripts,
                        transcriptAvailableLanguages: this.sortByValue(this.transcriptAvailableLanguages),
                        edxVideoID: this.edxVideoID,
                        transcriptClientTitle: this.getTranscriptClientTitle(),
                        transcriptDownloadFileFormat: this.videoTranscriptSettings.trancript_download_file_format
                    })
                );
                return this;
            }
        });

        return VideoTranscriptsView;
    }
);
