import {connect} from 'react-redux';

import Main from './Main.jsx';
import {fetchCourseBlocks, selectBlock} from '../../data/actions/courseBlocks';

const mapStateToProps = state => ({
    selectedBlock: state.selectedBlock,
});


const mapDispatchToProps = dispatch => ({
    onSelectBlock: blockId => dispatch(selectBlock(blockId)),
    fetchCourseBlocks: (courseId, excludeBlockTypes) =>
        dispatch(fetchCourseBlocks(courseId, excludeBlockTypes))
});

const MainContainer = connect(
    mapStateToProps,
    mapDispatchToProps,
)(Main);

export default MainContainer;
