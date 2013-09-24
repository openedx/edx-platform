(function (window, undefined) {
    Transcripts.Utils = (function () {
        var Storage = {};

        /**
        * @function
        *
        * Adds some data to the Storage object. If data with existent `data_id`
        * is added, nothing happens.
        *
        * @param {string} data_id Unique identifier for the data.
        * @param {any} data Data that should be stored.
        *
        * @returns {object} Object itself for chaining.
        */
        Storage.set = function (data_id, data) {
            Storage[data_id] = data;

            return this;
        };

        /**
        * @function
        *
        * Return data from the Storage object by identifier.
        *
        * @param {string} data_id Unique identifier of the data.
        *
        * @returns {any} Stored data.
        */
        Storage.get= function (data_id) {

            return Storage[data_id];
        };


        /**
        * @function
        *
        * Deletes data from the Storage object by identifier.
        *
        * @param {string} data_id Unique identifier of the data.
        *
        * @returns {boolean} Boolean value that indicate if data is removed.
        */
        Storage.remove = function (data_id) {

            return (delete Storage[data_id]);
        };

        /**
        * @function
        *
        * Returns model from collection by 'field_name' property.
        *
        * @param {object} collection The model (CMS.Models.Metadata) containing
        *                            information about metadata setting editors.
        * @param {string} field_name Name of field that should be found.
        *
        * @returns {
        *    object:        when model exist,
        *    undefined:     when model doesn't exist.
        * }
        */
        var _getField = function (collection, field_name) {
            var model;

            if (collection && field_name) {
                model = collection.findWhere({
                    field_name: field_name
                });
            }

            return model;
        };

        /**
        * @function
        *
        * Parses Youtube link and return video id.
        *
        * These are the types of URLs supported:
        * http://www.youtube.com/watch?v=OEoXaMPEzfM&feature=feedrec_grec_index
        * http://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/OEoXaMPEzfM
        * http://www.youtube.com/v/OEoXaMPEzfM?fs=1&amp;hl=en_US&amp;rel=0
        * http://www.youtube.com/watch?v=OEoXaMPEzfM#t=0m10s
        * http://www.youtube.com/embed/OEoXaMPEzfM?rel=0
        * http://www.youtube.com/watch?v=OEoXaMPEzfM
        * http://youtu.be/OEoXaMPEzfM
        *
        * @param {string} url Url that should be parsed.
        *
        * @returns {
        *    string:        Video Id,
        *    undefined:     when url has incorrect format or argument is
        *                   non-string, video id's length is not equal 11.
        * }
        */
        var _youtubeParser = (function () {
            var cache = {};

            return function (url) {
                if (typeof url !== 'string') {

                    return void(0);
                }

                if (cache[url]) {
                    return cache[url];
                }

                var regExp = /.*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*/;
                var match = url.match(regExp);
                cache[url] = (match && match[1].length === 11) ? match[1] : void(0);

                return cache[url];
            };
        }());

        /**
        * @function
        *
        * Parses links with html5 video sources in mp4 or webm formats.
        *
        * @param {string} url Url that should be parsed.
        *
        * @returns {
        *    object:        Object with information about the video
        *                   (file name, video type),
        *    undefined:     when url has incorrect format or argument is
        *                   non-string.
        * }
        */
        var _videoLinkParser = (function () {
            var cache = {};

            return function (url) {
                if (typeof url !== 'string') {

                    return void(0);
                }

                if (cache[url]) {
                    return cache[url];
                }

                var link = document.createElement('a'),
                    match;

                link.href = url;
                match = link.pathname
                            .split('/')
                            .pop()
                            .match(/(.+)\.(mp4|webm)$/);

                if (match) {
                    cache[url] = {
                        video: match[1],
                        type: match[2]
                    };
                }

                return cache[url];
            };
        }());

        /**
        * @function
        *
        * Facade function that parses html5 and youtube links.
        *
        * @param {string} url Url that should be parsed.
        *
        * @returns {
        *    object:        Object with information about the video:
        *                   {
        *                       mode: "youtube|html5|incorrect",
        *                       video: "file_name|youtube_id",
        *                       type: "youtube|mp4|webm"
        *                   },
        *    undefined:     when argument is non-string.
        * }
        */
        var _linkParser = function (url) {
            var result;

            if (typeof url !== 'string') {
                console.log('Transcripts.Utils.parseLink');
                console.log('TypeError: Wrong argument type.');

                return void(0);
            }

            if (_youtubeParser(url)) {
                result = {
                    mode: 'youtube',
                    video: _youtubeParser(url),
                    type: 'youtube'
                };
            } else if (_videoLinkParser(url)) {
                result = $.extend({mode: 'html5'}, _videoLinkParser(url));
            } else {
                result = {
                    mode: 'incorrect'
                };
            }

            return result;
        };

        /**
        * @function
        *
        * Returns short-hand youtube url.
        *
        * @param {string} video_id Youtube Video Id that will be added to the link.
        *
        * @returns {string} Short-hand Youtube url.
        *
        * @example
        * _getYoutubeLink('OEoXaMPEzfM'); => 'http://youtu.be/OEoXaMPEzfM'
        */
        var _getYoutubeLink = function (video_id) {
            return 'http://youtu.be/' + video_id;
        };

        /**
        * @function
        *
        * Synchronizes 2 Backbone collections by 'field_name' property.
        *
        * @param {object} fromCollection Collection with which synchronization
        *                                will happens.
        * @param {object} toCollection Collection which will synchronized.
        *
        */
        var _syncCollections = function (fromCollection, toCollection) {
            fromCollection.each(function (m) {
                var model = toCollection.findWhere({
                        field_name: m.getFieldName()
                    });

                if (model) {
                    model.setValue(m.getDisplayValue());
                }
            });
        };

        /**
        * @function
        *
        * Sends Ajax requests in appropriate format.
        *
        * @param {string} action Action that will be invoked on server. Is a part
        *                        of url.
        * @param {string} component_id Id of component.
        * @param {array} videoList List of object with information about inserted
        *                          urls.
        * @param {object} extraParams Extra parameters that can be send to the
        *                             server
        *
        * @returns {object} XMLHttpRequest object. Using this object, we can attach
        *    callbacks to AJAX request events (for example on 'done', 'fail',
        *    etc.).
        */
        var _command = (function () {
            // We will store the XMLHttpRequest object that $.ajax() function
            // returns, to abort an ongoing AJAX request (if necessary) upon
            // subsequent invocations of _command() function.
            //
            // A new AJAX request will be made on each invocation of the
            // _command() function.
            var xhr = null;

            return function (action, component_id, videoList, extraParams) {
                var params, data;

                console.log('[_command]: arguments = ', arguments);

                if (extraParams) {
                    if ($.isPlainObject(extraParams)) {
                        params = extraParams;
                    } else {
                        params = {params: extraParams};
                    }
                }

                data = $.extend(
                    { id: component_id },
                    { videos: videoList },
                    params
                );

                if (xhr && xhr.abort) {
                    xhr.abort();
                }

                xhr = $.ajax({
                    url: '/transcripts/' + action,
                    data: { data: JSON.stringify(data) },
                    notifyOnError: false,
                    type: 'get'
                });

                return xhr;
            };
        }());

        return {
            getField: _getField,
            parseYoutubeLink: _youtubeParser,
            parseHTML5Link: _videoLinkParser,
            parseLink: _linkParser,
            getYoutubeLink: _getYoutubeLink,
            syncCollections: _syncCollections,
            command: _command,
            Storage: {
                set: Storage.set,
                get: Storage.get,
                remove: Storage.remove
            }
        };
    }());
}(this));
