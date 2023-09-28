define(['js/models/custom_sync_xblock_info'],
    function(CustomSyncXBlockInfo) {
        var XBlockOutlineInfo = CustomSyncXBlockInfo.extend({

            urlRoots: {
                read: '/xblock/outline'
            },

            createChild: function(response) {
                return new XBlockOutlineInfo(response, {parse: true});
            }
        });
        return XBlockOutlineInfo;
    });
