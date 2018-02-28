import { connect } from 'react-redux';

import EntitlementSupportTable from './EntitlementSupportTable.jsx';

const mapStateToProps = state => ({
  entitlements: state.entitlements,
});

const EntitlementSupportTableContainer = connect(
  mapStateToProps,
)(EntitlementSupportTable);

export default EntitlementSupportTableContainer;
