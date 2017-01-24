define(['js/models/xblock_info'],
    function(XBlockInfo) {
        var CustomSyncXBlockInfo = XBlockInfo.extend({
            sync: function(method, model, options) {
                options.url = (this.urlRoots[method] || this.urlRoot) + '/' + this.get('id');
                return XBlockInfo.prototype.sync.call(this, method, model, options);
            }
        });
        return CustomSyncXBlockInfo;
    });
