// eslint-disable-next-line no-undef
define(['backbone', 'js/models/component_template'], function(Backbone, ComponentTemplate) {
    return Backbone.Collection.extend({
        model: ComponentTemplate
    });
});
