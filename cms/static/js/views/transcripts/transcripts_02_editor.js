(function (window, undefined) {
    Transcripts.Editor = Backbone.View.extend({

        tagName: 'div',

        initialize: function () {
            // prepare data for CMS.Views.Metadata.Editor

            var metadata = this.$el.data('metadata'),
                models = this.toModels(metadata);

            this.collection = new CMS.Models.MetadataCollection(models);

            // inititlaize CMS.Views.Metadata.Editor
            this.metadataEditor = new CMS.Views.Metadata.Editor({
                el: this.$el,
                collection: this.collection
            });
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
        toModels: function (data) {
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
        syncBasicTab: function (metadataCollection) {
            var result = [],
                utils = Transcripts.Utils,
                getField = utils.getField,
                values = {},
                videoUrl;

            // If metadataCollection is not passed, just exit.
            if (!metadataCollection) {
                return false;
            }

            // Get values from `Advanced` tab fields (`html5_sources`,
            // `youtube_id_1_0`) that should be synchronized.
            values.html5Sources = getField(metadataCollection, 'html5_sources')
                                    .getDisplayValue();

            values.youtube = getField(metadataCollection, 'youtube_id_1_0')
                                    .getDisplayValue();

            // Get field that should be synchronized with `Advanced` tab fields.
            videoUrl = getField(this.collection, 'video_url');

            // The length of youtube video_id should be 11 characters.
            if (values.youtube.length === 11) {
                // Just video id is retrieved from `Advanced` tab field and
                // it should be transformed to appropriate format.
                // OEoXaMPEzfM => http://youtu.be/OEoXaMPEzfM
                values.youtube = utils.getYoutubeLink(values.youtube);
            } else {
                values.youtube = '';
            }

            result.push(values.youtube);
            result = result.concat(values.html5Sources);

            videoUrl.setValue(result);

            // Synchronize other fields that has the same `field_name` property.
            utils.syncCollections(metadataCollection, this.collection);
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
        syncAdvancedTab: function (metadataCollection) {
            var utils = Transcripts.Utils,
                getField = utils.getField,
                subsValue = utils.Storage.get('sub'),
                subs = getField(metadataCollection, 'sub'),
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
                function (value) {
                    return utils.parseLink(value).mode;
                }
            );

            if (html5Sources) {
                html5Sources.setValue(result.html5 || []);
            }

            if (youtube) {
                if (result.youtube) {
                    result = utils.parseLink(result.youtube[0]).video;
                } else {
                    result = '';
                }

                youtube.setValue(result);
            }

            // If utils.Storage contain some subtitles, update them.
            if (_.isString(subsValue)) {
                subs.setValue(subsValue);
                // After updating should be removed, because it might overwrite
                // subtitles added by user manually.
                utils.Storage.remove('sub');
            }

            // Synchronize other fields that has the same `field_name` property.
            utils.syncCollections(this.collection, metadataCollection);
        }

    });
}(this));
