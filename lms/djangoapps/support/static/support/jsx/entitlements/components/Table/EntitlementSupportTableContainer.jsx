import { connect } from 'react-redux';

import { openReissueForm } from '../../data/actions/form';
import EntitlementSupportTable from './EntitlementSupportTable.jsx';

const mapStateToProps = state => ({
  entitlements: state.entitlements,
});

const mapDispatchToProps = dispatch => ({
  openReissueForm: entitlement => dispatch(openReissueForm(entitlement)),
});

const EntitlementSupportTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(EntitlementSupportTable);

export default EntitlementSupportTableContainer;
