/**
 * Simple model for adding a component of a given type (for example, "video" or "html").
 */
define(["backbone"], function (Backbone) {
    return Backbone.Model.extend({
        defaults: {
            type: "",
            // Each entry in the template array is an Object with the following keys:
            // display_name
            // category (may or may not match "type")
            // boilerplate_name (may be null)
            // is_common (only used for problems)
            templates: []
        },
        parse: function (response) {
            // Returns true only for templates that both have no boilerplate and are of
            // the overall type of the menu. This allows other component types to be added
            // and they will get sorted alphabetically rather than just at the top.
            // e.g. The ORA openassessment xblock is listed as an advanced problem.
            var isPrimaryBlankTemplate = function(template) {
                return !template.boilerplate_name && template.category === response.type;
            };

            this.type = response.type;
            this.templates = response.templates;
            this.display_name = response.display_name;

            // Sort the templates.
            this.templates.sort(function (a, b) {
                // The blank problem for the current type goes first
                if (isPrimaryBlankTemplate(a)) {
                    return -1;
                } else if (isPrimaryBlankTemplate(b)) {
                    return 1;
                // Hinted problems should be shown at the end
                } else if (a.hinted && !b.hinted) {
                    return 1;
                } else if (!a.hinted && b.hinted) {
                    return -1;
                } else if (a.display_name > b.display_name) {
                    return 1;
                } else if (a.display_name < b.display_name) {
                    return -1;
                }
                return 0;
            });
        }
    });
});
