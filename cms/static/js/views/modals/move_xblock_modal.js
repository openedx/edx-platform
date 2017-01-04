/**
 * The MoveXblockModal to move XBlocks in course.
 */
define([
    'jquery', 'backbone', 'underscore', 'gettext',
    'js/views/baseview', 'js/views/modals/base_modal',
    'common/js/components/views/feedback',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/move-xblock-modal.underscore'
],
function($, Backbone, _, gettext, BaseView, BaseModal, Feedback, StringUtils, MoveXblockModalTemplate) {
    'use strict';

    var MoveXblockModal = BaseModal.extend({
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
            this.XBlockUrlRoot = this.options.sourceXBlockInfo;
            this.options.title = this.getTitle();
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
            BaseModal.prototype.hide.apply(this);
            Feedback.prototype.outFocus.apply(this);
        }
    });

    return MoveXblockModal;
});
