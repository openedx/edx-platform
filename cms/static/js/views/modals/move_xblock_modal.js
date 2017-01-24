/**
 * The MoveXblockModal to move XBlocks in course.
 */
define([
    'jquery',
    'backbone',
    'underscore',
    'gettext',
    'js/views/baseview',
    'js/views/utils/xblock_utils',
    'js/views/utils/move_xblock_utils',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'common/js/components/views/feedback',
    'js/models/xblock_info',
    'js/views/modals/base_modal',
    'js/views/move_xblock_list',
    'js/views/move_xblock_breadcrumb',
    'text!templates/move-xblock-modal.underscore'
],
function($, Backbone, _, gettext, BaseView, XBlockViewUtils, MoveXBlockUtils, HtmlUtils, StringUtils, Feedback,
         XBlockInfoModel, BaseModal, MoveXBlockListView, MoveXBlockBreadcrumbView, MoveXblockModalTemplate) {
    'use strict';

    var MoveXblockModal = BaseModal.extend({
        events: _.extend({}, BaseModal.prototype.events, {
            'click .action-move:not(.is-disabled)': 'moveXBlock'
        }),

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'move-xblock',
            modalSize: 'lg',
            showEditorModeButtons: false,
            addPrimaryActionButton: true,
            primaryActionButtonType: 'move',
            viewSpecificClasses: 'move-modal',
            primaryActionButtonTitle: gettext('Move'),
            modalSRTitle: gettext('Choose a location to move your component to')
        }),

        initialize: function() {
            var self = this;
            BaseModal.prototype.initialize.call(this);
            this.listenTo(Backbone, 'move:breadcrumbRendered', this.focusModal);
            this.sourceXBlockInfo = this.options.sourceXBlockInfo;
            this.sourceParentXBlockInfo = this.options.sourceParentXBlockInfo;
            this.targetParentXBlockInfo = null;
            this.XBlockURLRoot = this.options.XBlockURLRoot;
            this.XBlockAncestorInfoURL = StringUtils.interpolate(
                '{urlRoot}/{usageId}?fields=ancestorInfo',
                {urlRoot: this.XBlockURLRoot, usageId: this.sourceXBlockInfo.get('id')}
            );
            this.outlineURL = this.options.outlineURL;
            this.options.title = this.getTitle();
            this.fetchCourseOutline().done(function(courseOutlineInfo, ancestorInfo) {
                $('.ui-loading').addClass('is-hidden');
                $('.breadcrumb-container').removeClass('is-hidden');
                self.renderViews(courseOutlineInfo, ancestorInfo);
            });
            this.movedAlertView = null;
            this.isValidMove = false;
            this.listenTo(Backbone, 'move:enableMoveOperation', this.enableMoveOperation);
        },

        getTitle: function() {
            return StringUtils.interpolate(
                gettext('Move: {displayName}'),
                {displayName: this.sourceXBlockInfo.get('display_name')}
            );
        },

        getContentHtml: function() {
            return _.template(MoveXblockModalTemplate)({});
        },

        show: function() {
            BaseModal.prototype.show.apply(this, [false]);
            this.updateMoveState(false);
            MoveXBlockUtils.hideMovedNotification();
        },

        hide: function() {
            if (this.moveXBlockListView) {
                this.moveXBlockListView.remove();
            }
            if (this.moveXBlockBreadcrumbView) {
                this.moveXBlockBreadcrumbView.remove();
            }
            BaseModal.prototype.hide.apply(this);
            Feedback.prototype.outFocus.apply(this);
        },

        focusModal: function() {
            Feedback.prototype.inFocus.apply(this, [this.options.modalWindowClass]);
            $(this.options.modalWindowClass).focus();
        },

        fetchCourseOutline: function() {
            return $.when(
                this.fetchData(this.outlineURL),
                this.fetchData(this.XBlockAncestorInfoURL)
            );
        },

        fetchData: function(url) {
            var deferred = $.Deferred();
            $.ajax({
                url: url,
                contentType: 'application/json',
                dataType: 'json',
                type: 'GET'
            }).done(function(data) {
                deferred.resolve(data);
            }).fail(function() {
                deferred.reject();
            });
            return deferred.promise();
        },

        renderViews: function(courseOutlineInfo, ancestorInfo) {
            this.moveXBlockBreadcrumbView = new MoveXBlockBreadcrumbView({});
            this.moveXBlockListView = new MoveXBlockListView(
                {
                    model: new XBlockInfoModel(courseOutlineInfo, {parse: true}),
                    ancestorInfo: ancestorInfo
                }
            );
        },

        updateMoveState: function(isValidMove) {
            var $moveButton = this.$el.find('.action-move');
            if (isValidMove) {
                $moveButton.removeClass('is-disabled');
            } else {
                $moveButton.addClass('is-disabled');
            }
        },

        enableMoveOperation: function(targetParentXBlockInfo) {
            var isValidMove = false,
                sourceParentType = this.sourceParentXBlockInfo.get('category'),
                targetParentType = targetParentXBlockInfo.get('category');

            if (targetParentType === sourceParentType && this.sourceParentXBlockInfo.id !== targetParentXBlockInfo.id) {
                isValidMove = true;
                this.targetParentXBlockInfo = targetParentXBlockInfo;
            }
            this.updateMoveState(isValidMove);
        },

        moveXBlock: function() {
            var self = this;
            XBlockViewUtils.moveXBlock(self.sourceXBlockInfo.id, self.targetParentXBlockInfo.id)
            .done(function(response) {
                // hide modal
                self.hide();
                // hide xblock element
                $("li.studio-xblock-wrapper[data-locator='" + self.sourceXBlockInfo.id + "']").hide();
                self.movedAlertView = MoveXBlockUtils.showMovedNotification(
                    StringUtils.interpolate(
                        gettext('Success! "{displayName}" has been moved.'),
                        {
                            displayName: self.sourceXBlockInfo.get('display_name')
                        }
                    ),
                    {
                        sourceDisplayName: self.sourceXBlockInfo.get('display_name'),
                        sourceLocator: self.sourceXBlockInfo.id,
                        sourceParentLocator: self.sourceParentXBlockInfo.id,
                        targetParentLocator: response.parent_locator,
                        targetIndex: response.source_index
                    }
                );
            });
        }
    });

    return MoveXblockModal;
});
