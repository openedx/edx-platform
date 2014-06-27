define(["jquery", "underscore", "js/views/xblock_outline"],
    function($, _, XBlockOutlineView) {

        var CourseOutlineView = XBlockOutlineView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                XBlockOutlineView.prototype.initialize.call(this);
            },

            shouldRenderChildren: function() {
                // Render all nodes up to verticals but not below
                return this.model.get('category') !== 'vertical';
            },

            createChildView: function(xblockInfo, parentInfo) {
                return new CourseOutlineView({
                    model: xblockInfo,
                    parentInfo: parentInfo,
                    template: this.template
                });
            }
        });

        return CourseOutlineView;
    }); // end define();
