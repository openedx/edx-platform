define(
    ['jquery', 'backbone', 'js/views/active_video_upload_list', 'js/views/previous_video_upload_list'],
    function($, Backbone, ActiveVideoUploadListView, PreviousVideoUploadListView) {
        'use strict';
        var VideosIndexFactory = function(
            $contentWrapper,
            postUrl,
            encodingsDownloadUrl,
            concurrentUploadLimit,
            uploadButton,
            previousUploads
        ) {
            var activeView = new ActiveVideoUploadListView({
                postUrl: postUrl,
                concurrentUploadLimit: concurrentUploadLimit,
                uploadButton: uploadButton
            });
            $contentWrapper.append(activeView.render().$el);
            var previousCollection = new Backbone.Collection(previousUploads);
            var previousView = new PreviousVideoUploadListView({
                collection: previousCollection,
                encodingsDownloadUrl: encodingsDownloadUrl
            });
            $contentWrapper.append(previousView.render().$el);
        };

        return VideosIndexFactory;
    }
);
