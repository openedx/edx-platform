const findBlockWithId = (blockList, blockId) => {
    if (!blockList) return;
    for (let block of blockList) {
        if (block.id === blockId) return block;
        else {
            const foundBlock = findBlockWithId(block.children, blockId);
            if (foundBlock) return foundBlock;
        }
    }
};

export const getActiveBlockTree = (state) => {
    console.log(state.rootBlock, state.blocks);
    if (state.rootBlock === state.blocks.id) return state.blocks;
    return findBlockWithId(state.blocks.children, state.rootBlock);
};