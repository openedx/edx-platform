/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
