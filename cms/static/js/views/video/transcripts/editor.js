define(
    [
        'jquery', 'backbone', 'underscore',
        'js/views/video/transcripts/utils',
        'js/views/metadata', 'js/collections/metadata',
        'js/views/video/transcripts/metadata_videolist'
    ],
function($, Backbone, _, Utils, MetadataView, MetadataCollection) {
    var Editor = Backbone.View.extend({

        tagName: 'div',

        initialize: function() {
            // prepare data for MetadataView.Editor

            var metadata = this.$el.data('metadata'),
                models = this.toModels(metadata);

            this.collection = new MetadataCollection(models);

            // initialize MetadataView.Editor
            this.settingsView = new MetadataView.Editor({
                el: this.$el,
                collection: this.collection
            });

            // Listen to edx_video_id update
            this.listenTo(Backbone, 'transcripts:basicTabUpdateEdxVideoId', this.handleUpdateEdxVideoId);
        },

        /**
        * @function
        *
        * Convert JSON metadata to List of models
        *
        * @param {object|string} data Data containing information about metadata
        *                             setting editors.
        *
        * @returns {array} Processed objects list.
        *
        * @example:
        * var metadata = {
        *       field_1: {.1.},
        *       field_2: {.2.}
        *    };
        *
        * toModels(metadata) // => [{.1.}, {.2.}]
        *
        */
        toModels: function(data) {
            var metadata = (_.isString(data)) ? JSON.parse(data) : data,
                models = [];

            for (var model in metadata) {
                if (metadata.hasOwnProperty(model)) {
                    models.push(metadata[model]);
                }
            }

            return models;
        },

        /**
        * @function
        *
        * Synchronize data from `Advanced` tab of Video player with data in
        * `Basic` tab. It is called when we go from `Advanced` to `Basic` tab.
        *
        * @param {object} metadataCollection Collection containing all models
        *                                    with information about metadata
        *                                    setting editors in `Advanced` tab.
        *
        */
        syncBasicTab: function(metadataCollection, metadataView) {
            var result = [],
                getField = Utils.getField,
                component_locator = this.$el.closest('[data-locator]').data('locator'),
                values = {},
                videoUrl, metadata, modifiedValues;

            // If metadataCollection is not passed, just exit.
            if (!metadataCollection || !metadataView) {
                return false;
            }

            // Get field that should be synchronized with `Advanced` tab fields.
            videoUrl = getField(this.collection, 'video_url');

            modifiedValues = metadataView.getModifiedMetadataValues();

            // Get values from `Advanced` tab fields (`html5_sources`,
            // `youtube_id_1_0`) that should be synchronized.
            var html5Sources = getField(metadataCollection, 'html5_sources').getDisplayValue();

            values.youtube = getField(metadataCollection, 'youtube_id_1_0').getDisplayValue();

            values.html5Sources = _.filter(html5Sources, function(value) {
                var link = Utils.parseLink(value),
                    mode = link && link.mode;

                return mode === 'html5' && mode;
            });


            // The length of youtube video_id should be 11 characters.
            if (values.youtube.length === 11) {
                // Just video id is retrieved from `Advanced` tab field and
                // it should be transformed to appropriate format.
                // OEoXaMPEzfM => http://youtu.be/OEoXaMPEzfM
                values.youtube = Utils.getYoutubeLink(values.youtube);
            } else {
                values.youtube = '';
            }

            result.push(values.youtube);
            result = result.concat(values.html5Sources);

            videoUrl.setValue(result);

            // Synchronize other fields that has the same `field_name` property.
            Utils.syncCollections(metadataCollection, this.collection);
        },

        /**
        * @function
        *
        * Synchronize data from `Basic` tab of Video player with data in
        * `Advanced` tab. It is called when we go from `Basic` to `Advanced` tab.
        *
        * @param {object} metadataCollection Collection containing all models
        *                                    with information about metadata
        *                                    setting editors in `Advanced` tab.
        *
        */
        syncAdvancedTab: function(metadataCollection, metadataView) {
            var getField = Utils.getField,
                html5Sources, youtube, videoUrlValue, result;

            // if metadataCollection is not passed, just exit.
            if (!metadataCollection) {
                return false;
            }

            // Get fields from `Advenced` tab (`html5_sources`, `youtube_id_1_0`)
            // that should be synchronized.
            html5Sources = getField(metadataCollection, 'html5_sources');

            youtube = getField(metadataCollection, 'youtube_id_1_0');

            // Get value from `Basic` tab `VideoUrl` field that should be
            // synchronized.
            videoUrlValue = getField(this.collection, 'video_url')
                                .getDisplayValue();

            // Change list representation format to more convenient and group
            // them by mode (`youtube`, `html5`).
            //                  Before:
            // [
            //      'http://youtu.be/OEoXaMPEzfM',
            //      'video_name.mp4',
            //      'video_name.webm'
            // ]
            //                  After:
            // {
            //      youtube: [{mode: `youtube`, type: `youtube`, ...}],
            //      html5: [
            //          {mode: `html5`, type: `mp4`, ...},
            //          {mode: `html5`, type: `webm`, ...}
            //      ]
            // }
            result = _.groupBy(
                videoUrlValue,
                function(value) {
                    return Utils.parseLink(value).mode;
                }
            );

            if (html5Sources) {
                html5Sources.setValue(result.html5 || []);
            }

            if (youtube) {
                if (result.youtube) {
                    result = Utils.parseLink(result.youtube[0]).video;
                } else {
                    result = '';
                }

                youtube.setValue(result);
            }

            // Synchronize other fields that has the same `field_name` property.
            Utils.syncCollections(this.collection, metadataCollection);
        },

        handleUpdateEdxVideoId: function(edxVideoId) {
            var edxVideoIdField = Utils.getField(this.collection, 'edx_video_id');
            Utils.Storage.set('edx_video_id', Utils.getEdxVideoIdData(edxVideoId));
            edxVideoIdField.setValue(edxVideoId);
        }

    });

    return Editor;
});
