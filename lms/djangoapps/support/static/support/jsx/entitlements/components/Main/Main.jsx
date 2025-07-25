import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, Alert } from '@openedx/paragon';
import SearchContainer from '../Search/SearchContainer';
import EntitlementSupportTableContainer from '../Table/EntitlementSupportTableContainer';
import EntitlementFormContainer from '../EntitlementForm/container';

// eslint-disable-next-line react/function-component-definition
const Main = props => (
    <div className="entitlement-support-wrapper">
        <Alert
            variant="danger"
            onClose={props.dismissErrorMessage}
            show={!!props.errorMessage}
            dismissible
        >
            {props.errorMessage}
        </Alert>
        <h2>
            Student Support: Entitlement
        </h2>
        <MainContent
            isFormOpen={props.isFormOpen}
            ecommerceUrl={props.ecommerceUrl}
            openCreationForm={props.openCreationForm}
            entitlements={props.entitlements}
        />
    </div>
);

// eslint-disable-next-line react/function-component-definition
const MainContent = (props) => {
    if (props.isFormOpen) {
        return <EntitlementFormContainer />;
    }

    return (
        <div>
            <div className="actions">
                <SearchContainer />
                <Button
                    variant="primary"
                    onClick={props.openCreationForm}
                >
                    Create New Entitlement
                </Button>
            </div>
            {
                props.entitlements.length > 0
                    ? <EntitlementSupportTableContainer ecommerceUrl={props.ecommerceUrl} /> : null
            }
        </div>
    );
};

const mapStateToProps = state => ({
    entitlements: state.entitlements,
});

Main.propTypes = {
    errorMessage: PropTypes.string.isRequired,
    dismissErrorMessage: PropTypes.func.isRequired,
    openCreationForm: PropTypes.func.isRequired,
    ecommerceUrl: PropTypes.string.isRequired,
    isFormOpen: PropTypes.bool.isRequired,
    entitlements: PropTypes.arrayOf(PropTypes.string).isRequired,
};

MainContent.propTypes = {
    openCreationForm: PropTypes.func.isRequired,
    ecommerceUrl: PropTypes.string.isRequired,
    isFormOpen: PropTypes.bool.isRequired,
    entitlements: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default connect(mapStateToProps, null)(Main);
