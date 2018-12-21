import { fetchCourseBlocks, selectBlock } from 'BlockBrowser/data/actions/courseBlocks';
import { connect } from 'react-redux';

import Main from './Main';

const mapStateToProps = state => ({
  selectedBlock: state.selectedBlock,
});


const mapDispatchToProps = dispatch => ({
  onSelectBlock: blockId => dispatch(selectBlock(blockId)),
  fetchCourseBlocks: (courseId, excludeBlockTypes) =>
    dispatch(fetchCourseBlocks(courseId, excludeBlockTypes)),
});

const MainContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Main);

export default MainContainer;
