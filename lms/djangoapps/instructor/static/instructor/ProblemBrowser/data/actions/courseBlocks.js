import {courseBlocksActions} from './constants';
import {getCourseBlocks} from "../api/client";

const fetchCourseBlocksSuccess = blocks => ({
    type: courseBlocksActions.fetch.SUCCESS,
    blocks,
});

const selectBlock = blockId => ({
    type: courseBlocksActions.SELECT_BLOCK,
    blockId,
});

const changeRoot = blockId => ({
    type: courseBlocksActions.CHANGE_ROOT,
    blockId,
});

const fetchCourseBlocks = courseId => (dispatch) =>
    getCourseBlocks(courseId)
        .then((response) => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(response);
        })
        .then(
            json => dispatch(fetchCourseBlocksSuccess(json)),
            error => console.log(error),
        );

export {
    fetchCourseBlocks,
    fetchCourseBlocksSuccess,
    selectBlock,
    changeRoot,
};
