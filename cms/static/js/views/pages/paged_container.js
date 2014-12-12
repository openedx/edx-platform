/**
 * PagedXBlockContainerPage is a variant of XBlockContainerPage that supports Pagination.
 */
define(["jquery", "underscore", "gettext", "js/views/pages/container", "js/views/paged_container"],
    function ($, _, gettext, XBlockContainerPage, PagedContainerView) {
        'use strict';
        var PagedXBlockContainerPage = XBlockContainerPage.extend({

            defaultViewClass: PagedContainerView,
            components_on_init: false,

            initialize: function (options){
                this.page_size = options.page_size || 10;
                XBlockContainerPage.prototype.initialize.call(this, options);
            },

            getViewParameters: function () {
               return  _.extend(XBlockContainerPage.prototype.getViewParameters.call(this), {
                   page_size: this.page_size,
                   page: this
               });
            },

            refreshXBlock: function(element, block_added) {
                var xblockElement = this.findXBlockElement(element),
                    rootLocator = this.xblockView.model.id;
                if (xblockElement.length === 0 || xblockElement.data('locator') === rootLocator) {
                    this.render({refresh: true, block_added: block_added});
                } else {
                    this.refreshChildXBlock(xblockElement, block_added);
                }
            }

        });
        return PagedXBlockContainerPage;
    });
