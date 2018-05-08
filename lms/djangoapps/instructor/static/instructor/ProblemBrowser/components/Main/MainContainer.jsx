import { fetchCourseBlocks, selectBlock } from 'BlockBrowser/data/actions/courseBlocks';
import { connect } from 'react-redux';
import { createProblemResponsesReportTask, reset } from '../../data/actions/problemResponses';
import Main from './Main';

const mapStateToProps = state => ({
  selectedBlock: state.selectedBlock,
  timeout: state.popupTask.timeout,
});


const mapDispatchToProps = dispatch => ({
  onSelectBlock: blockId => dispatch(selectBlock(blockId)),
  fetchCourseBlocks:
    (courseId, excludeBlockTypes) =>
      dispatch(fetchCourseBlocks(courseId, excludeBlockTypes)),
  createProblemResponsesReportTask:
    (initialEndpoint, taskStatusEndpoint, problemLocation) =>
      dispatch(
        createProblemResponsesReportTask(initialEndpoint, taskStatusEndpoint, problemLocation),
      ),
  resetProblemResponsesReportTask: () => dispatch(reset),
});

const MainContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Main);

export default MainContainer;
