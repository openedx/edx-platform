define(["jquery", "underscore", "js/views/baseview"],
    function($, _, BaseView) {

        var XBlockOutlineView = BaseView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.template = this.options.template;
                if (!this.template) {
                    this.template = this.loadTemplate('xblock-outline');
                }
                this.parentInfo = this.options.parentInfo;
            },

            render: function() {
                var i, children, listElement, childOutlineView;
                if (this.parentInfo) {
                    this.renderTemplate();
                }
                if (this.shouldRenderChildren()) {
                    listElement = this.$('.sortable-list');
                    children = this.model.get('children');
                    for (i=0; i < children.length; i++) {
                        childOutlineView = this.createChildView(children[i], this.model);
                        childOutlineView.render();
                        listElement.append(childOutlineView.$('li').first());
                    }
                }
                return this;
            },

            shouldRenderChildren: function() {
                return true;
            },

            createChildView: function(xblockInfo, parentInfo) {
                return new XBlockOutlineView({
                    model: xblockInfo,
                    parentInfo: parentInfo,
                    template: this.template
                });
            },

            renderTemplate: function() {
                var xblockInfo = this.model,
                    childInfo = xblockInfo.get('child_info'),
                    xblockType = this.getXBlockType(this.model.get('category'), this.parentInfo),
                    parentType = this.getXBlockType(this.parentInfo.get('category'));
                this.$el.html(this.template({
                    xblockInfo: xblockInfo,
                    parentInfo: this.parentInfo,
                    xblockType: xblockType,
                    parentType: parentType,
                    childType: childInfo ? this.getXBlockType(childInfo.category, xblockInfo) : null,
                    childCategory: childInfo ? childInfo.category : null,
                    childTypeDisplayName: childInfo ? childInfo.display_name : null,
                    includesChildren: this.shouldRenderChildren()
                }));
            },

            getXBlockType: function(category, parentInfo) {
                var xblockType = category;
                if (category === 'chapter') {
                    xblockType = 'section';
                } else if (category === 'sequential') {
                    xblockType = 'subsection';
                } else if (category === 'vertical' && parentInfo && parentInfo.get('category') === 'sequential') {
                    xblockType = 'unit';
                }
                return xblockType;
            }
        });

        return XBlockOutlineView;
    }); // end define();
