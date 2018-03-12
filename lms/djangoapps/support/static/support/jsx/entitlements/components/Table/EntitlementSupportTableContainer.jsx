import { connect } from 'react-redux';

import { openReissueModal } from '../../data/actions/modal';
import EntitlementSupportTable from './EntitlementSupportTable.jsx';

const mapStateToProps = state => ({
  entitlements: state.entitlements,
});

const mapDispatchToProps = dispatch => ({
  openReissueModal: entitlement => dispatch(openReissueModal(entitlement)),
});

const EntitlementSupportTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(EntitlementSupportTable);

export default EntitlementSupportTableContainer;
