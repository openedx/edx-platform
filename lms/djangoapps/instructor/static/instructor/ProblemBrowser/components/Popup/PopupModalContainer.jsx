import { connect } from 'react-redux';
import PopupModal from './PopupModal';

const mapStateToProps = state => ({
  selectedBlock: state.selectedBlock,
  error: state.popupTask.error,
  message: state.popupTask.message,
  inProgress: state.popupTask.inProgress,
  succeeded: state.popupTask.succeeded,
  reportPath: state.popupTask.reportPath,
  reportPreview: state.popupTask.reportPreview,
  timeout: state.popupTask.timeout,
});

export const PopupModalContainer = connect(
    mapStateToProps,
)(PopupModal);

export default PopupModalContainer;
