define(["backbone", "js/models/asset"], function(Backbone, AssetModel){
  var AssetCollection = Backbone.Collection.extend({
     model : AssetModel
  });
  return AssetCollection;
});
