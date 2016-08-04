/* globals URI */

(function(URI) {
    'use strict';

    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            var key;
            for (key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function Ctor() {
                this.constructor = child;
            }
            Ctor.prototype = parent.prototype;
            child.prototype = new Ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    this.LmsRuntime = {};

    this.LmsRuntime.v1 = (function(_super) {

        __extends(v1, _super);

        function v1() {
            return v1.__super__.constructor.apply(this, arguments);
        }

        v1.prototype.handlerUrl = function(element, handlerName, suffix, query, thirdparty) {
            var courseId, handlerAuth, uri, usageId;
            courseId = $(element).data('course-id');
            usageId = $(element).data('usage-id');
            handlerAuth = thirdparty ? 'handler_noauth' : 'handler';
            uri = URI('/courses')
                .segment(courseId)
                .segment('xblock')
                .segment(usageId)
                .segment(handlerAuth)
                .segment(handlerName);
            if (suffix !== null) {
                uri.segment(suffix);
            }
            if (query !== null) {
                uri.search(query);
            }
            return uri.toString();
        };

        return v1;

    })(XBlock.Runtime.v1);
}).call(this, URI);
