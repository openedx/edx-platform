/**
 * The UnitOutlineChildView is used to render each Section,
 * Subsection, and Unit within the Unit Outline component on the unit
 * page.
 */
define(['underscore', 'js/views/xblock_outline'],
    function(_, XBlockOutlineView) {
        var UnitOutlineChildView = XBlockOutlineView.extend({
            initialize: function() {
                XBlockOutlineView.prototype.initialize.call(this);
                this.currentUnitId = this.options.currentUnitId;
            },

            getTemplateContext: function() {
                return _.extend(
                    XBlockOutlineView.prototype.getTemplateContext.call(this),
                    {currentUnitId: this.currentUnitId}
                );
            },

            getChildViewClass: function() {
                return UnitOutlineChildView;
            },

            createChildView: function(childInfo, parentInfo, options) {
                options = _.isUndefined(options) ? {} : options;
                return XBlockOutlineView.prototype.createChildView.call(
                    this, childInfo, parentInfo, _.extend(options, {currentUnitId: this.currentUnitId})
                );
            }
        });

        return UnitOutlineChildView;
    }); // end define()
