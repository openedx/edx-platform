import { getCourseBlocks } from '../api/client';
import courseBlocksActions from './constants';

const fetchCourseBlocksSuccess = (blocks, excludeBlockTypes) => ({
    type: courseBlocksActions.fetch.SUCCESS,
    blocks,
    excludeBlockTypes,
});

const selectBlock = blockId => ({
    type: courseBlocksActions.SELECT_BLOCK,
    blockId,
});

const changeRoot = blockId => ({
    type: courseBlocksActions.CHANGE_ROOT,
    blockId,
});

const fetchCourseBlocks = (courseId, excludeBlockTypes) => dispatch =>
    getCourseBlocks(courseId)
        .then((response) => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(response);
        })
        .then(
            json => dispatch(fetchCourseBlocksSuccess(json, excludeBlockTypes)),
            error => console.log(error), // eslint-disable-line no-console
        );

export {
    fetchCourseBlocks,
    fetchCourseBlocksSuccess,
    selectBlock,
    changeRoot,
};
