;(function (define) {
    'use strict';
    define([
        'underscore',
        'common/js/components/views/paging_header',
        'text!teams/templates/topic-header-message.underscore'
    ], function (_, PagingHeader, headerMessageTemplate) {
        var TopicHeader = PagingHeader.extend({
            messageHtml: function () {
                return _.template(headerMessageTemplate, {
                    currentItemRange: this.currentItemRangeLabel(),
                    totalItemsCount: this.totalItemsCountLabel()
                });
            }
        });
        return TopicHeader;
    });
}).call(this, define || RequireJS.define);
