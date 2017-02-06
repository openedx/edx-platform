define([
    'jquery', 'underscore', 'backbone', 
    'gettext',
    'js/views/baseview',
    'js/views/paging',
    'js/views/previous_video_upload',
    'common/js/components/views/paging_footer',
    'common/js/components/views/paging_header'],

    function($, _, Backbone, gettext, BaseView, PagingView,
        PreviousVideoUploadView, PagingFooter, PagingHeader) {
        'use strict';
        var PreviousVideoUploadListView = BaseView.extend({
            tagName: 'section',
            className: 'wrapper-assets',

            initialize: function(options) {
                this.pagingView = new this.PreviousVideoUploadPagingView({
                    el: this.$el,
                    collection: this.collection,
                    encodingsDownloadUrl: options.encodingsDownloadUrl,
                    videoHandlerUrl: options.videoHandlerUrl,
                    template: this.loadTemplate('previous-video-upload-list')
                });
            },

            PreviousVideoUploadPagingView: PagingView.extend({
                initialize: function(options){
                    Backbone.View.prototype.initialize.call(this);
                    this.encodingsDownloadUrl = options.encodingsDownloadUrl;
                    this.videoHandlerUrl = options.videoHandlerUrl;
                    this.template = options.template;
                },

                render: function(){
                    var videoHandlerUrl = this.videoHandlerUrl;
                    this.itemViews = this.collection.map(function(model) {
                        return new PreviousVideoUploadView({
                            model: model,
                            videoHandlerUrl: videoHandlerUrl,
                        });
                    });

                    var $el = this.$el,
                    $tabBody;
                    $el.html(this.template({encodingsDownloadUrl: this.encodingsDownloadUrl}));
                    $tabBody = $el.find('.js-table-body');
                    _.each(this.itemViews, function(view) {
                                   $tabBody.append(view.render().$el);
                    });
                    this.pagingHeader = new PagingHeader({el: $el.find('#video-paging-header'),
                        collection: this.collection});
                    this.pagingFooter = new PagingFooter({collection: this.collection,
                        el: $el.find('#video-paging-footer')});
                    this.pagingHeader.render();
                    this.pagingFooter.render();
                },

            }),

            render: function() {
                this.pagingView.render();
                return this;
            }
        });

        return PreviousVideoUploadListView;
    }
);
