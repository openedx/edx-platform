/**
 * PagedXBlockContainerPage is a variant of XBlockContainerPage that supports Pagination.
 */
define(['jquery', 'underscore', 'gettext', 'js/views/pages/container', 'js/views/paged_container'],
    function($, _, gettext, XBlockContainerPage, PagedContainerView) {
        'use strict';
        var PagedXBlockContainerPage = XBlockContainerPage.extend({

            events: _.extend({}, XBlockContainerPage.prototype.events, {
                'click .toggle-preview-button': 'toggleChildrenPreviews'
            }),

            defaultViewClass: PagedContainerView,
            components_on_init: false,

            initialize: function(options) {
                this.page_size = options.page_size || 10;
                this.showChildrenPreviews = options.showChildrenPreviews || true;
                XBlockContainerPage.prototype.initialize.call(this, options);
            },

            getViewParameters: function() {
                return _.extend(XBlockContainerPage.prototype.getViewParameters.call(this), {
                    page_size: this.page_size,
                    page: this
                });
            },

            refreshXBlock: function(element, block_added, is_duplicate) {
                var xblockElement = this.findXBlockElement(element),
                    rootLocator = this.xblockView.model.id;
                if (xblockElement.length === 0 || xblockElement.data('locator') === rootLocator) {
                    this.render({refresh: true, block_added: block_added});
                } else {
                    this.refreshChildXBlock(xblockElement, block_added, is_duplicate);
                }
            },

            toggleChildrenPreviews: function(xblockElement) {
                xblockElement.preventDefault();
                this.xblockView.togglePreviews();
            },

            updatePreviewButton: function(show_previews) {
                var text = (show_previews) ? gettext('Hide Previews') : gettext('Show Previews'),
                    button = $('.nav-actions .button-toggle-preview');

                this.$('.preview-text', button).text(text);
                this.$('.toggle-preview-button').removeClass('is-hidden');
            }
        });
        return PagedXBlockContainerPage;
    });
