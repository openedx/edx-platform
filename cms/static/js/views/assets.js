<<<<<<< HEAD
define(["backbone", "js/views/asset"], function(Backbone, AssetView) {
=======
"use strict";
// This code is temporarily moved out of asset_index.html
// to fix AWS pipelining issues. We can move it back after RequireJS is integrated.
$(document).ready(function() {
    $('.uploads .upload-button').bind('click', showUploadModal);
    $('.upload-modal .close-button').bind('click', hideModal);
    $('.upload-modal .choose-file-button').bind('click', showFileSelectionMenu);
});

var showUploadModal = function (e) {
    e.preventDefault();
    resetUploadModal();
    // $modal has to be global for hideModal to work.
    $modal = $('.upload-modal').show();
    $('.file-input').bind('change', startUpload);
    $('.upload-modal .file-chooser').fileupload({
        dataType: 'json',
        type: 'POST',
        maxChunkSize: 100 * 1000 * 1000,      // 100 MB
        autoUpload: true,
        progressall: function(e, data) {
            var percentComplete = parseInt((100 * data.loaded) / data.total, 10);
            showUploadFeedback(e, percentComplete);
        },
        maxFileSize: 100 * 1000 * 1000,   // 100 MB
        maxNumberofFiles: 100,
        add: function(e, data) {
            data.process().done(function () {
                data.submit();
            });
        },
        done: function(e, data) {
            displayFinishedUpload(data.result);
        }

    });

    $modalCover.show();
};

var showFileSelectionMenu = function(e) {
    e.preventDefault();
    $('.file-input').click();
};

var startUpload = function (e) {
    var file = e.target.value;

    $('.upload-modal h1').html(gettext('Uploading…'));
    $('.upload-modal .file-name').html(file.substring(file.lastIndexOf("\\") + 1));
    $('.upload-modal .choose-file-button').hide();
    $('.upload-modal .progress-bar').removeClass('loaded').show();
};
>>>>>>> Hook up js to css classes

var AssetsView = Backbone.View.extend({
    // takes AssetCollection as model

    initialize : function() {
        this.listenTo(this.collection, 'destroy', this.handleDestroy);
        this.render();
    },

    render: function() {
        this.$el.empty();

        var self = this;
        this.collection.each(
            function(asset) {
                var view = new AssetView({model: asset});
                self.$el.append(view.render().el);
            });

        return this;
    },

    handleDestroy: function(model, collection, options) {
        var index = options.index;
        this.$el.children().eq(index).remove();

        analytics.track('Deleted Asset', {
            'course': course_location_analytics,
            'id': model.get('url')
        });
    },

    addAsset: function (model) {
        // If asset is not already being shown, add it.
        if (this.collection.findWhere({'url': model.get('url')}) === undefined) {
            this.collection.add(model, {at: 0});
            var view = new AssetView({model: model});
            this.$el.prepend(view.render().el);

            analytics.track('Uploaded a File', {
                'course': course_location_analytics,
                'asset_url': model.get('url')
            });
        }
    }
});

return AssetsView;
}); // end define();
