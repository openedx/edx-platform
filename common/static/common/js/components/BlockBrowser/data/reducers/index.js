import { combineReducers } from 'redux';
import courseBlocksActions from '../actions/constants';

export const buildBlockTree = (blocks, excludeBlockTypes) => {
    if (!(blocks && blocks.root)) { return null; }
    const blockTree = (root, parent) => {
        // eslint-disable-next-line prefer-object-spread
        const tree = Object.assign({ parent }, blocks.blocks[root]);
        if (tree.children) {
            tree.children = tree.children.map(block => blockTree(block, root));
            if (excludeBlockTypes) {
                tree.children = tree.children.filter(
                    block => !excludeBlockTypes.includes(block.type),
                );
            }
        }
        return tree;
    };
    return blockTree(blocks.root, null);
};

// eslint-disable-next-line default-param-last
export const blocks = (state = {}, action) => {
    switch (action.type) {
    case courseBlocksActions.fetch.SUCCESS:
        return buildBlockTree(action.blocks, action.excludeBlockTypes);
    default:
        return state;
    }
};

// eslint-disable-next-line default-param-last
export const selectedBlock = (state = '', action) => {
    switch (action.type) {
    case courseBlocksActions.SELECT_BLOCK:
        return action.blockId;
    default:
        return state;
    }
};

// eslint-disable-next-line default-param-last
export const rootBlock = (state = null, action) => {
    switch (action.type) {
    case courseBlocksActions.fetch.SUCCESS:
        return action.blocks.root;
    case courseBlocksActions.CHANGE_ROOT:
        return action.blockId;
    default:
        return state;
    }
};

export default combineReducers({
    blocks,
    selectedBlock,
    rootBlock,
});
