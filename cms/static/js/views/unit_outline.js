/**
 * The UnitOutlineView is used to render the Unit Outline component on the unit page. It shows
 * the ancestors of the unit along with its direct siblings. It also has a single "New Unit"
 * button to allow a new sibling unit to be added.
 */
define(['underscore', 'js/views/xblock_outline', 'js/views/unit_outline_child'],
    function(_, XBlockOutlineView, UnitOutlineChildView) {
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
                    for (i = ancestors.length - 1; i >= 0; i--) {
                        ancestor = ancestors[i];
                        ancestorView = this.createChildView(
                            ancestor,
                            previousAncestor,
                            {parentView: ancestorView, currentUnitId: this.model.get('id')}
                        );
                        ancestorView.render();
                        listElement.append(ancestorView.$el);
                        previousAncestor = ancestor;
                        listElement = ancestorView.getListElement();
                    }
                }
                return ancestorView;
            },

            getChildViewClass: function() {
                return UnitOutlineChildView;
            },

            getTemplateContext: function() {
                return _.extend(
                    XBlockOutlineView.prototype.getTemplateContext.call(this),
                    {currentUnitId: this.model.get('id')}
                );
            }
        });

        return UnitOutlineView;
    }); // end define();
