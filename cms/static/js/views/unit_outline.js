/**
 * The UnitOutlineView is used to render the Unit Outline component on the unit page. It shows
 * the ancestors of the unit along with its direct siblings. It also has a single "New Unit"
 * button to allow a new sibling unit to be added.
 */
define(['js/views/xblock_outline'],
    function(XBlockOutlineView) {

        var UnitOutlineView = XBlockOutlineView.extend({
            // takes XBlockInfo as a model

            templateName: 'unit-outline',

            render: function() {
                XBlockOutlineView.prototype.render.call(this);
                this.renderAncestors();
                return this;
            },

            renderAncestors: function() {
                var i, listElement,
                    ancestors, ancestor, ancestorView = this,
                    previousAncestor = null;
                if (this.model.get('ancestor_info')) {
                    ancestors = this.model.get('ancestor_info').ancestors;
                    listElement = this.getListElement();
                    // Note: the ancestors are processed in reverse order because the tree wants to
                    // start at the root, but the ancestors are ordered by closeness to the unit,
                    // i.e. subsection and then section.
                    for (i=ancestors.length - 1; i >= 0; i--) {
                        ancestor = ancestors[i];
                        ancestorView = this.createChildView(ancestor, previousAncestor, ancestorView);
                        ancestorView.render();
                        listElement.append(ancestorView.$el);
                        previousAncestor = ancestor;
                        listElement = ancestorView.getListElement();
                    }
                }
                return ancestorView;
            }
        });

        return UnitOutlineView;
    }); // end define();
