define(["backbone", "gettext", "backbone.associations"], function(Backbone, gettext) {
    var Chapter = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: "",
                asset_path: "",
                order: this.collection ? this.collection.nextOrder() : 1
            };
        },
        isEmpty: function() {
            return !this.get('name') && !this.get('asset_path');
        },
        parse: function(response) {
            if("title" in response && !("name" in response)) {
                response.name = response.title;
                delete response.title;
            }
            if("url" in response && !("asset_path" in response)) {
                response.asset_path = response.url;
                delete response.url;
            }
            return response;
        },
        toJSON: function() {
            return {
                title: this.get('name'),
                url: this.get('asset_path')
            };
        },
        // NOTE: validation functions should return non-internationalized error
        // messages. The messages will be passed through gettext in the template.
        validate: function(attrs, options) {
            if(!attrs.name && !attrs.asset_path) {
                return {
                    message: gettext("Chapter name and asset_path are both required"),
                    attributes: {name: true, asset_path: true}
                };
            } else if(!attrs.name) {
                return {
                    message: gettext("Chapter name is required"),
                    attributes: {name: true}
                };
            } else if (!attrs.asset_path) {
                return {
                    message: gettext("asset_path is required"),
                    attributes: {asset_path: true}
                };
            }
        }
    });
    return Chapter;
});
