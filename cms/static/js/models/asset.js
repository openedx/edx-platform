define(['backbone'], function(Backbone) {
  /**
   * Simple model for an asset.
   */
    var Asset = Backbone.Model.extend({
        defaults: {
            display_name: '',
            content_type: '',
            thumbnail: '',
            date_added: '',
            url: '',
            external_url: '',
            portable_url: '',
            locked: false
        },
        get_extension: function() {
            var name_segments = this.get('display_name').split('.').reverse();
            var asset_type = (name_segments.length > 1) ? name_segments[0].toUpperCase() : '';
            return asset_type;
        }
    });
    return Asset;
});
