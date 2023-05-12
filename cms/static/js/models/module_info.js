// eslint-disable-next-line no-undef
define(['backbone', 'js/utils/module'], function(Backbone, ModuleUtils) {
    // eslint-disable-next-line no-var
    var ModuleInfo = Backbone.Model.extend({
        urlRoot: ModuleUtils.urlRoot,

        defaults: {
            id: null,
            data: null,
            metadata: null,
            children: null
        }
    });
    return ModuleInfo;
});
