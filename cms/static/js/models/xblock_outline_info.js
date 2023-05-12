// eslint-disable-next-line no-undef
define(['js/models/custom_sync_xblock_info'],
    function(CustomSyncXBlockInfo) {
        // eslint-disable-next-line no-var
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
