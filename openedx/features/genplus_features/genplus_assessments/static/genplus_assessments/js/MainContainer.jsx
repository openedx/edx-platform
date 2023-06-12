import { selectBlock } from 'BlockBrowser/data/actions/courseBlocks';
import { fetchCourseBlocks } from './data/actions/courseBlocks';
import { connect } from 'react-redux';
import Main from './Main';

const mapStateToProps = state => ({
  selectedBlock: state.selectedBlock,
});


const mapDispatchToProps = dispatch => ({
  onSelectBlock: blockId => dispatch(selectBlock(blockId)),
  fetchCourseBlocks:
    (baseUrl, courseId, excludeBlockTypes) =>
      dispatch(fetchCourseBlocks(baseUrl, courseId, excludeBlockTypes))
});

const MainContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Main);

export default MainContainer;
