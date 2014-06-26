define(["jquery", "underscore", "js/views/baseview"],
    function($, _, BaseView) {

        var XBlockOutlineView = BaseView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                this.template = this.loadTemplate('xblock-outline');
                this.parentInfo = this.options.parentInfo;
            },

            render: function() {
                var i, children, listElement, listItem, childOutlineView, xblockType, parentType,
                    childType, childCategory;
                if (this.parentInfo) {
                    xblockType = this.getXBlockType(this.model, this.parentInfo);
                    parentType = this.getXBlockType(this.parentInfo);
                    childType = this.getXBlockChildType(this.model);
                    childCategory = childType;
                    if (childCategory === 'unit') {
                        childCategory = 'vertical';
                    } else if (childType === 'subsection') {
                        childCategory = 'sequential';
                    } else if (childType === 'section') {
                        childCategory = 'chapter';
                    }
                    this.$el.html(this.template({
                        xblockInfo: this.model,
                        parentInfo: this.parentInfo,
                        xblockType: xblockType,
                        parentType: parentType,
                        childType: childType,
                        childCategory: childCategory
                    }));
                }
                listElement = this.$('.sortable-list');
                children = this.model.get('children');
                for (i=0; i < children.length; i++) {
                    childOutlineView = new XBlockOutlineView({
                        model: children[i],
                        parentInfo: this.model
                    });
                    listItem = $('<li></li>').appendTo(listElement);
                    listItem.append(childOutlineView.$el);
                    childOutlineView.render();
                }
                return this;
            },

            getXBlockType: function(xblockInfo, parentInfo) {
                var category = xblockInfo.get('category'),
                    xblockType = category;
                if (category === 'chapter') {
                    xblockType = 'section';
                } else if (category === 'sequential') {
                    xblockType = 'subsection';
                } else if (category === 'vertical' && parentInfo && parentInfo.get('category') === 'sequential') {
                    xblockType = 'unit';
                }
                return xblockType;
            },

            getXBlockChildType: function(xblockInfo) {
                var category = xblockInfo.get('category'),
                    childType = null;
                if (category === 'course') {
                    childType = 'section';
                } else if (category === 'section') {
                    childType = 'subsection';
                } else if (category === 'subsection') {
                    childType = 'unit';
                }
                return childType;
            }
        });

        return XBlockOutlineView;
    }); // end define();
