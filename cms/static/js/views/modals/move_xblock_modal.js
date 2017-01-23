/**
 * The MoveXblockModal to move XBlocks in course.
 */
define([
    'jquery', 'backbone', 'underscore', 'gettext',
    'js/views/baseview', 'js/views/modals/base_modal',
    'js/models/xblock_info', 'js/views/move_xblock_list', 'js/views/move_xblock_breadcrumb',
    'common/js/components/views/feedback',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/move-xblock-modal.underscore'
],
function($, Backbone, _, gettext, BaseView, BaseModal, XBlockInfoModel, MoveXBlockListView, MoveXBlockBreadcrumbView,
         Feedback, StringUtils, MoveXblockModalTemplate) {
    'use strict';

    var MoveXblockModal = BaseModal.extend({
        modalSRTitle: gettext('Choose a location to move your component to'),

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'move-xblock',
            modalSize: 'med',
            addPrimaryActionButton: true,
            primaryActionButtonType: 'move',
            primaryActionButtonTitle: gettext('Move')
        }),

        initialize: function() {
            BaseModal.prototype.initialize.call(this);
            this.sourceXBlockInfo = this.options.sourceXBlockInfo;
            this.XBlockUrlRoot = this.options.XBlockUrlRoot;
            this.outlineURL = this.options.outlineURL;
            this.options.title = this.getTitle();
            this.fetchCourseOutline();
        },

        getTitle: function() {
            return StringUtils.interpolate(
                gettext('Move: {display_name}'),
                {display_name: this.sourceXBlockInfo.get('display_name')}
            );
        },

        getContentHtml: function() {
            return _.template(MoveXblockModalTemplate)({});
        },

        show: function() {
            BaseModal.prototype.show.apply(this, [false]);
            Feedback.prototype.inFocus.apply(this, [this.options.modalWindowClass]);
        },

        hide: function() {
            this.moveXBlockListView.remove();
            this.moveXBlockBreadcrumbView.remove();
            BaseModal.prototype.hide.apply(this);
            Feedback.prototype.outFocus.apply(this);
        },

        fetchCourseOutline: function() {
            var self = this;
            $.ajax({
                url: this.outlineURL,
                contentType: 'application/json',
                dataType: 'json',
                type: 'GET'
            }).done(function(outlineJson) {
                $('.ui-loading').addClass('is-hidden');
                $('.breadcrumb-container').removeClass('is-hidden');
                self.renderViews(outlineJson);
            }).fail(function(jqXHR, textStatus, errorThrown) {
                // TODO! What to do here???
            });
        },

        renderViews: function(outlineJson) {
            debugger;
            this.moveXBlockBreadcrumbView = new MoveXBlockBreadcrumbView(
                {
                    el: '.breadcrumb-container'
                }
            );
            this.moveXBlockListView = new MoveXBlockListView(
                {
                    el: '.xblock-list-container',
                    model: new XBlockInfoModel(outlineJson, {parse: true})
                }
            );
        }
    });

    return MoveXblockModal;
});
