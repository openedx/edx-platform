// eslint-disable-next-line no-undef
define(['backbone'], function(Backbone) {
    /**
   * Simple model for an asset.
   */
    // eslint-disable-next-line no-var
    var Asset = Backbone.Model.extend({
        defaults: {
            display_name: '',
            content_type: '',
            thumbnail: '',
            date_added: '',
            url: '',
            external_url: '',
            portable_url: '',
            locked: false,
            static_full_url: '',
        },
        get_extension: function() {
            /* eslint-disable-next-line camelcase, no-var */
            var name_segments = this.get('display_name').split('.').reverse();
            /* eslint-disable-next-line camelcase, no-var */
            var asset_type = (name_segments.length > 1) ? name_segments[0].toUpperCase() : '';
            // eslint-disable-next-line camelcase
            return asset_type;
        }
    });
    return Asset;
});
