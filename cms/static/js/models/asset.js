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
      external_url: "",
      portable_url: "",
      locked: false
    }
  });
  return Asset;
});
