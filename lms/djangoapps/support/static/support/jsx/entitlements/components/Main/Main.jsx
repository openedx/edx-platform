import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, StatusAlert } from '@edx/paragon';
import SearchContainer from '../Search/SearchContainer';
import EntitlementSupportTableContainer from '../Table/EntitlementSupportTableContainer';
import EntitlementFormContainer from '../EntitlementForm/container';

const Main = props => (
    <div className="entitlement-support-wrapper">
        <StatusAlert
            alertType="danger"
            dialog={props.errorMessage}
            onClose={props.dismissErrorMessage}
            open={!!props.errorMessage}
        />
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

const MainContent = (props) => {
    if (props.isFormOpen) {
        return <EntitlementFormContainer />;
    }

    return (
        <div>
            <div className="actions">
                <SearchContainer />
                <Button
                    className={['btn', 'btn-primary']}
                    label="Create New Entitlement"
                    onClick={props.openCreationForm}
                />
            </div>
            {
                props.entitlements.length > 0 ?
                    <EntitlementSupportTableContainer ecommerceUrl={props.ecommerceUrl} /> : null
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
