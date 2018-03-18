import {connect} from 'react-redux';

import Main from './Main.jsx';
import {selectBlock, fetchCourseBlocks} from "../../data/actions/courseBlocks";

const mapStateToProps = state => ({
    selectedBlock: state.selectedBlock,
});


const mapDispatchToProps = dispatch => ({
    onSelectBlock: blockId => dispatch(selectBlock(blockId)),
    fetchCourseBlocks: courseId => dispatch(fetchCourseBlocks(courseId)),
});

const MainContainer = connect(
    mapStateToProps,
    mapDispatchToProps,
)(Main);

export default MainContainer;
