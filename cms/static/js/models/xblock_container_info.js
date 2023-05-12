// eslint-disable-next-line no-undef
define(['js/models/custom_sync_xblock_info'],
    function(CustomSyncXBlockInfo) {
        // eslint-disable-next-line no-var
        var XBlockContainerInfo = CustomSyncXBlockInfo.extend({
            urlRoots: {
                read: '/xblock/container'
            }
        });
        return XBlockContainerInfo;
    });
