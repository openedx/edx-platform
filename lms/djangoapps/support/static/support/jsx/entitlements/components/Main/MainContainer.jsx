/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { connect } from 'react-redux';

import { dismissError } from '../../data/actions/error';
import { openCreationForm } from '../../data/actions/form';

import Main from './Main.jsx';

const mapStateToProps = state => ({
    errorMessage: state.error,
    isFormOpen: state.form.isOpen,
});

const mapDispatchToProps = dispatch => ({
    dismissErrorMessage: () => dispatch(dismissError()),
    openCreationForm: () => dispatch(openCreationForm()),
});

const MainContainer = connect(
    mapStateToProps,
    mapDispatchToProps,
)(Main);

export default MainContainer;
