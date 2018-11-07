import React from 'react';
import PropTypes from 'prop-types';

import { Button, StatusAlert } from '@edx/paragon';
import SearchContainer from '../Search/SearchContainer.jsx';
import EntitlementSupportTableContainer from '../Table/EntitlementSupportTableContainer.jsx';
import EntitlementFormContainer from '../EntitlementForm/container.jsx';

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
      <EntitlementSupportTableContainer ecommerceUrl={props.ecommerceUrl} />
    </div>
  );
};

Main.propTypes = {
  errorMessage: PropTypes.string.isRequired,
  dismissErrorMessage: PropTypes.func.isRequired,
  openCreationForm: PropTypes.func.isRequired,
  ecommerceUrl: PropTypes.string.isRequired,
  isFormOpen: PropTypes.bool.isRequired,
};

MainContent.propTypes = {
  openCreationForm: PropTypes.func.isRequired,
  ecommerceUrl: PropTypes.string.isRequired,
  isFormOpen: PropTypes.bool.isRequired,
};

export default Main;
