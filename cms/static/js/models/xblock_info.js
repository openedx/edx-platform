define(["backbone", "js/utils/module"], function(Backbone, ModuleUtils) {
    var XBlockInfo = Backbone.Model.extend({

        urlRoot: ModuleUtils.urlRoot,

        defaults: {
            "id": null,
            "display_name": null,
            "category": null,
            "is_draft": null,
            "is_container": null,
            "data": null,
            "metadata" : null,
            "children": null,
            "studio_url": null,
            "child_info": null
        },

        parse: function (response) {
            var i, rawChildren, children;
            rawChildren = response.children;
            children = [];
            if (rawChildren) {
                for (i=0; i < rawChildren.length; i++) {
                    children.push(new XBlockInfo(rawChildren[i], { parse: true }));
                }
            }
            response.children = children;
            return response;
        }
    });
    return XBlockInfo;
});
