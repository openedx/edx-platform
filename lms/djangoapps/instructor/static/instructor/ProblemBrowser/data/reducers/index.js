import {combineReducers} from 'redux';
import {courseBlocksActions} from '../actions/constants';

const BLOCK_TYPES = ['course', 'chapter', 'sequential', 'vertical', 'problem'];

export const buildBlockTree = (blocks) => {
    if (!(blocks && blocks.root)) return null;
    const blockTree = (root, parent) => {
        const tree = Object.assign({parent}, blocks.blocks[root]);
        if (tree.children) {
            tree.children = tree.children
                .map(block => blockTree(block, root))
                .filter(block => BLOCK_TYPES.includes(block.type));
        }
        return tree;
    };
    return blockTree(blocks.root, null);
};

const blocks = (state = {}, action) => {
    switch (action.type) {
        case courseBlocksActions.fetch.SUCCESS:
            return buildBlockTree(action.blocks);
        default:
            return state;
    }
};

const selectedBlock = (state = null, action) => {
    switch (action.type) {
        case courseBlocksActions.SELECT_BLOCK:
            return action.blockId;
        default:
            return state;
    }
};


const rootBlock = (state = null, action) => {
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
