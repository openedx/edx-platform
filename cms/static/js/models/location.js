define(["backbone", "underscore"], function(Backbone, _) {
    var Location = Backbone.Model.extend({
        defaults: {
            tag: "",
            org: "",
            course: "",
            category: "",
            name: ""
        },
        toUrl: function(overrides) {
            return
                (overrides && overrides['tag'] ? overrides['tag'] : this.get('tag')) + "://" +
                (overrides && overrides['org'] ? overrides['org'] : this.get('org')) + "/" +
                (overrides && overrides['course'] ? overrides['course'] : this.get('course')) + "/" +
                (overrides && overrides['category'] ? overrides['category'] : this.get('category')) + "/" +
                (overrides && overrides['name'] ? overrides['name'] : this.get('name')) + "/";
        },
        _tagPattern : /[^:]+/g,
        _fieldPattern : new RegExp('[^/]+','g'),

        parse: function(payload) {
            if (_.isArray(payload)) {
                return {
                    tag: payload[0],
                    org: payload[1],
                    course: payload[2],
                    category: payload[3],
                    name: payload[4]
                };
            }
            else if (_.isString(payload)) {
                this._tagPattern.lastIndex = 0; // odd regex behavior requires this to be reset sometimes
                var foundTag = this._tagPattern.exec(payload);
                if (foundTag) {
                    this._fieldPattern.lastIndex = this._tagPattern.lastIndex + 1; // skip over the colon
                    return {
                        tag: foundTag[0],
                        org: this.getNextField(payload),
                        course: this.getNextField(payload),
                        category: this.getNextField(payload),
                        name: this.getNextField(payload)
                    };
                }
                else return null;
            }
            else {
                return payload;
            }
        },
        getNextField : function(payload) {
            try {
                return this._fieldPattern.exec(payload)[0];
            }
            catch (err) {
                return "";
            }
        }
    });
    return Location;
});
