import { fetchCourseBlocks, selectBlock } from 'BlockBrowser/data/actions/courseBlocks';
import { connect } from 'react-redux';
import { createProblemResponsesReportTask } from '../../data/actions/problemResponses';
import Main from './Main';

const mapStateToProps = state => ({
    selectedBlock: state.selectedBlock,
});


const mapDispatchToProps = dispatch => ({
    onSelectBlock: blockId => dispatch(selectBlock(blockId)),
    fetchCourseBlocks:
    (courseId, excludeBlockTypes) =>
        dispatch(fetchCourseBlocks(courseId, excludeBlockTypes)),
    createProblemResponsesReportTask:
    (problemResponsesEndpoint, taskStatusEndpoint, reportDownloadEndpoint, problemLocation) =>
        dispatch(
            createProblemResponsesReportTask(
                problemResponsesEndpoint, taskStatusEndpoint, reportDownloadEndpoint, problemLocation,
            ),
        ),
});

const MainContainer = connect(
    mapStateToProps,
    mapDispatchToProps,
)(Main);

export default MainContainer;
