define(["backbone", "js/models/xblock_type"],
    function(Backbone, XBlockType) {
        var XBlockTypes = Backbone.Collection.extend({
            model: XBlockType,

            parse: function(response) {
                var xblockTypes = [],
                    xblockTypeJson, i;
                for (i=0; i < response.xblock_types.length; i++) {
                    xblockTypeJson = response.xblock_types[i];
                    xblockTypes.push(new XBlockType(xblockTypeJson));
                }
                return xblockTypes;
            }

        });
        return XBlockTypes;
    });
