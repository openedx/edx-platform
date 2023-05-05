/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { connect } from 'react-redux';

import { fetchEntitlements } from '../../data/actions/entitlement';
import Search from './Search.jsx';

const mapStateToProps = state => ({
    entitlements: state.entitlements,
});

const mapDispatchToProps = dispatch => ({
    fetchEntitlements: username => dispatch(fetchEntitlements(username)),
});

const SearchContainer = connect(
    mapStateToProps,
    mapDispatchToProps,
)(Search);

export default SearchContainer;
