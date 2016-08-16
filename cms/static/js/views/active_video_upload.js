define(
    ['js/models/active_video_upload', 'js/views/baseview'],
    function(ActiveVideoUpload, BaseView) {
        'use strict';

        var STATUS_CLASSES = [
            {status: ActiveVideoUpload.STATUS_QUEUED, cls: 'queued'},
            {status: ActiveVideoUpload.STATUS_COMPLETED, cls: 'success'},
            {status: ActiveVideoUpload.STATUS_FAILED, cls: 'error'}
        ];

        var ActiveVideoUploadView = BaseView.extend({
            tagName: 'li',
            className: 'active-video-upload',

            initialize: function() {
                this.template = this.loadTemplate('active-video-upload');
                this.listenTo(this.model, 'change', this.render);
            },

            render: function() {
                var $el = this.$el;
                $el.html(this.template(this.model.attributes));
                var status = this.model.get('status');
                _.each(
                    STATUS_CLASSES,
                    function(statusClass) {
                        $el.toggleClass(statusClass.cls, status == statusClass.status);
                    }
                );
                return this;
            }
        });

        return ActiveVideoUploadView;
    }
);
