define(['jquery', 'underscore', 'jquery.ajaxQueue'], function($) {
'use strict';
return (function () {
    var Storage = {};

    /**
    * Adds some data to the Storage object. If data with existent `data_id`
    * is added, nothing happens.
    * @function
    * @param {String} data_id Unique identifier for the data.
    * @param {Any} data Data that should be stored.
    * @return {Object} Object itself for chaining.
    */
    Storage.set = function (data_id, data) {
        Storage[data_id] = data;

        return this;
    };

    /**
    * Return data from the Storage object by identifier.
    * @function
    * @param {String} data_id Unique identifier of the data.
    * @return {Any} Stored data.
    */
    Storage.get= function (data_id) {

        return Storage[data_id];
    };


    /**
    * Deletes data from the Storage object by identifier.
    * @function
    * @param {String} data_id Unique identifier of the data.
    * @return {Boolean} Boolean value that indicate if data is removed.
    */
    Storage.remove = function (data_id) {

        return (delete Storage[data_id]);
    };

    /**
    * Returns model from collection by 'field_name' property.
    * @function
    * @param {Object} collection The model (CMS.Models.Metadata) information
    * about metadata setting editors.
    * @param {String} field_name Name of field that should be found.
    * @return {
    *    Object:        When model exist.
    *    Undefined:     When model doesn't exist.
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
    * Parses Youtube link and return video id.
    * @function
    * These are the types of URLs supported:
    * http://www.youtube.com/watch?v=OEoXaMPEzfM&feature=feedrec_grec_index
    * http://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/OEoXaMPEzfM
    * http://www.youtube.com/v/OEoXaMPEzfM?fs=1&amp;hl=en_US&amp;rel=0
    * http://www.youtube.com/watch?v=OEoXaMPEzfM#t=0m10s
    * http://www.youtube.com/embed/OEoXaMPEzfM?rel=0
    * http://www.youtube.com/watch?v=OEoXaMPEzfM
    * http://youtu.be/OEoXaMPEzfM
    * @param {String} url Url that should be parsed.
    * @return {
    *    String:        Video Id.
    *    Undefined:     When url has incorrect format or argument is
    *                   non-string, video id's length is not equal 11.
    * }
    */
    var _youtubeParser = (function () {
        var cache = {},
            regExp = /(?:http|https|)(?:\:\/\/|)(?:www.|)(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{11})[a-z0-9;:@#?&%=+\/\$_.-]*/i;

        return function (url) {
            if (typeof url !== 'string') {

                return void(0);
            }

            if (cache[url]) {
                return cache[url];
            }

            var match = url.match(regExp);
            cache[url] = (match && match[1].length === 11) ?
                match[1] :
                void(0);

            return cache[url];
        };
    }());

    /**
    * Parses links with html5 video sources in mp4 or webm formats.
    * @function
    * @param {String} url Url that should be parsed.
    * @return {
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
                        .match(/(.+)\.(mp?4v?|webm)$/);

            if (match) {
                cache[url] = {
                    video: match[1],
                    type: match[2]
                };
            } /*else {
                cache[url] = {
                    video: link.pathname
                            .split('/')
                            .pop(),
                    type: 'other'
                };
            }*/

            return cache[url];
        };
    }());

    /**
    * Facade function that parses html5 and youtube links.
    * @function
    * @param {String} url Url that should be parsed.
    * @return {
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
    * Returns short-hand youtube url.
    * @function
    * @param {string} video_id Youtube Video Id that will be added to the
    * link.
    * @return {string} Short-hand Youtube url.
    * @examples
    * _getYoutubeLink('OEoXaMPEzfM'); => 'http://youtu.be/OEoXaMPEzfM'
    */
    var _getYoutubeLink = function (video_id) {
        return 'http://youtu.be/' + video_id;
    };

    /**
    * Returns list of objects with information about the passed links.
    * @function
    * @param {array} links List of links that will be processed.
    * @returns {array} List of objects.
    * @examples
    * var links = [
    *      'http://youtu.be/OEoXaMPEzfM',
    *      'video_name.mp4',
    *      'video_name.webm'
    * ]
    *
    * _getVideoList(links); // =>
    *     [
    *       {mode: `youtube`, type: `youtube`, ...},
    *       {mode: `html5`, type: `mp4`, ...},
    *       {mode: `html5`, type: `webm`, ...}
    *     ]
    */
    var _getVideoList = function (links) {
        if ($.isArray(links)) {
            var arr = [],
                data;

            for (var i = 0, len = links.length; i < len; i += 1) {
                data = _linkParser(links[i]);

                if (data.mode !== 'incorrect') {
                    arr.push(data);
                }
            }

            return arr;
        }
    };


    /**
    * Synchronizes 2 Backbone collections by 'field_name' property.
    * @function
    * @param {Object} fromCollection Collection with which synchronization will
    * happens.
    * @param {Object} toCollection Collection which will synchronized.
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
    * Sends Ajax requests in appropriate format.
    * @function
    * @param {String} action Action that will be invoked on server.
    * @param {String} component_locator the locator of component.
    * @param {Array} videoList List of object with information about inserted
    * urls.
    * @param {Object} extraParams Extra parameters that can be send to the
    * server.
    * @return {Object} XMLHttpRequest object. Using this object, we can
    * attach callbacks to AJAX request events (for example on 'done',
    * 'fail', etc.).
    */
    var _command = (function () {
        // We will store the XMLHttpRequest object that $.ajax() function
        // returns, to abort an ongoing AJAX request (if necessary) upon
        // subsequent invocations of _command() function.
        //
        // A new AJAX request will be made on each invocation of the
        // _command() function.
        var xhr = null;

        return function (action, locator, videoList, extraParams) {
            var params, data;

            if (extraParams) {
                if ($.isPlainObject(extraParams)) {
                    params = extraParams;
                } else {
                    params = {params: extraParams};
                }
            }

            data = $.extend(
                { locator: locator },
                { videos: videoList },
                params
            );

            xhr = $.ajaxQueue({
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
        getVideoList: _getVideoList,
        Storage: {
            set: Storage.set,
            get: Storage.get,
            remove: Storage.remove
        }
    };
}());
});
