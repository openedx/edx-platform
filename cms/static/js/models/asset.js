/**
 * Simple model for an asset.
 */
CMS.Models.Asset = Backbone.Model.extend({
    defaults: {
        display_name: "",
        thumbnail: "",
        date_added: "",
        url: "",
        portable_url: "",
        locked: false
    }
});
