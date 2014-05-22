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
            this.type = response.type;
            this.templates = response.templates;

            // Sort the templates.
            this.templates.sort(function (a, b) {
                // The entry without a boilerplate always goes first
                if (!a.boilerplate_name || (a.display_name < b.display_name)) {
                    return -1;
                }
                else {
                    return (a.display_name > b.display_name) ? 1 : 0;
                }
            });
        }
    });
});
