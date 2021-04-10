export const findBlockWithId = (blockList, blockId) => {
  if (!blockList) return null;
  for (let idx = 0; idx < blockList.length; idx += 1) {
    const block = blockList[idx];
    if (block.id === blockId) return block;

    const foundBlock = findBlockWithId(block.children, blockId);
    if (foundBlock) return foundBlock;
  }
  return null;
};

export const getActiveBlockTree = (state) => {
  if (state.rootBlock === state.blocks.id) return state.blocks;
  return findBlockWithId(state.blocks.children, state.rootBlock);
};
