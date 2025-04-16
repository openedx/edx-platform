import _ from 'underscore';

/**
 * Video Download Transcript control module.
 *
 * @constructor
 * @param {jQuery} element
 * @param {Object} options
 */
function VideoTranscriptDownloadHandler(element, options = {}) {
    if (!(this instanceof VideoTranscriptDownloadHandler)) {
        return new VideoTranscriptDownloadHandler(element, options);
    }

    _.bindAll(this, 'clickHandler');

    this.container = element;
    this.options = options;

    if (this.container.find('.wrapper-downloads .wrapper-download-transcripts')) {
        this.initialize();
    }
}

VideoTranscriptDownloadHandler.prototype = {
    // Initializes the module.
    initialize() {
        this.value = this.options.storage.getItem('transcript_download_format');
        this.el = this.container.find('.list-download-transcripts');
        this.el.on('click', '.btn-link', this.clickHandler);
    },

    // Event handler. We delay link clicks until the file type is set
    clickHandler(event) {
        event.preventDefault();

        const fileType = $(event.target).data('value');
        const data = {transcript_download_format: fileType};
        const downloadUrl = $(event.target).attr('href');

        $.ajax({
            url: this.options.saveStateUrl,
            type: 'POST',
            dataType: 'json',
            data: data,
            success: () => {
                this.options.storage.setItem('transcript_download_format', fileType);
            },
            complete: () => {
                document.location.href = downloadUrl;
            },
        });
    },
};

export {VideoTranscriptDownloadHandler};
