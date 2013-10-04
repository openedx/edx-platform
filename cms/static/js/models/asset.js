define(["backbone"], function(Backbone) {
  /**
   * Simple model for an asset.
   */
  var Asset = Backbone.Model.extend({
    defaults: {
      display_name: "",
      thumbnail: "",
      date_added: "",
      url: "",
      portable_url: "",
      locked: false
    }
  });
  return Asset;
});
