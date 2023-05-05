/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
