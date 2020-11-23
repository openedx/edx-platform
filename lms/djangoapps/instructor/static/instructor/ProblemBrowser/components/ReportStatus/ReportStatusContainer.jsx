import { connect } from 'react-redux';
import ReportStatus from './ReportStatus';

const mapStateToProps = state => ({
  selectedBlock: state.selectedBlock,
  error: state.reportStatus.error,
  inProgress: state.reportStatus.inProgress,
  succeeded: state.reportStatus.succeeded,
  reportPath: state.reportStatus.reportPath,
  timeout: state.reportStatus.timeout,
});

export const ReportStatusContainer = connect(
    mapStateToProps,
)(ReportStatus);

export default ReportStatusContainer;
