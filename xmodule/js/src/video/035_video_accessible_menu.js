(function(define) {
    'use strict';
    // VideoTranscriptDownloadHandler module.
    define(
        'video/035_video_accessible_menu.js', ['underscore'],
        function(_) {
            /**
     * Video Download Transcript control module.
     * @exports video/035_video_accessible_menu.js
     * @constructor
     * @param {jquery Element} element
     * @param {Object} options
     */
            var VideoTranscriptDownloadHandler = function(element, options) {
                if (!(this instanceof VideoTranscriptDownloadHandler)) {
                    return new VideoTranscriptDownloadHandler(element, options);
                }

                _.bindAll(this, 'clickHandler');

                this.container = element;
                this.options = options || {};

                if (this.container.find('.wrapper-downloads .wrapper-download-transcripts')) {
                    this.initialize();
                }

                return false;
            };

            VideoTranscriptDownloadHandler.prototype = {
                // Initializes the module.
                initialize: function() {
                    this.value = this.options.storage.getItem('transcript_download_format');
                    this.el = this.container.find('.list-download-transcripts');
                    this.el.on('click', '.btn-link', this.clickHandler);
                },

                // Event handler. We delay link clicks until the file type is set
                clickHandler: function(event) {
                    var that = this,
                        fileType,
                        data,
                        downloadUrl;

                    event.preventDefault();

                    fileType = $(event.target).data('value');
                    data = {transcript_download_format: fileType};
                    downloadUrl = $(event.target).attr('href');

                    $.ajax({
                        url: this.options.saveStateUrl,
                        type: 'POST',
                        dataType: 'json',
                        data: data,
                        success: function() {
                            that.options.storage.setItem('transcript_download_format', fileType);
                        },
                        complete: function() {
                            document.location.href = downloadUrl;
                        }
                    });
                }
            };

            return VideoTranscriptDownloadHandler;
        });
}(RequireJS.define));
