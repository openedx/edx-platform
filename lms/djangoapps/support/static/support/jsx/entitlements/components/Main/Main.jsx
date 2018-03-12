import React from 'react';
import PropTypes from 'prop-types';

import { Button, StatusAlert } from '@edx/paragon';
import SearchContainer from '../Search/SearchContainer.jsx';
import EntitlementSupportTableContainer from '../Table/EntitlementSupportTableContainer.jsx';
import EntitlementModalContainer from '../Modal/ModalContainer.jsx';

const Main = props => (
  <div>
    <StatusAlert
      alertType="danger"
      dialog={props.errorMessage}
      onClose={props.dismissErrorMessage}
      open={!!props.errorMessage}
    />
    <h2>
      Entitlement Support Page
    </h2>
    <SearchContainer />
    <Button
      className={['btn', 'btn-primary']}
      label= "Create New Entitlement"
      onClick={props.openCreationModal}
    />
    <EntitlementModalContainer />
    <EntitlementSupportTableContainer ecommerceUrl={props.ecommerceUrl} parentSelector='body'/>
  </div>
);

Main.propTypes = {
  errorMessage: PropTypes.string.isRequired,
  dismissErrorMessage: PropTypes.func.isRequired,
  openCreationModal: PropTypes.func.isRequired,
  ecommerceUrl: PropTypes.string.isRequired,
};

export default Main;
