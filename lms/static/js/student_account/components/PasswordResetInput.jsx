/* globals gettext */

import PropTypes from 'prop-types';
import React from 'react';

import { InputText } from '@edx/paragon/static';

function PasswordResetInput(props) {
  return (
    <div className="form-field">
      <InputText
        id={props.name}
        type="password"
        themes={['danger']}
        dangerIconDescription={gettext('Error: ')}
        required
        {...props}
      />
    </div>
  );
}

PasswordResetInput.propTypes = {
  name: PropTypes.string.isRequired,
};

export default PasswordResetInput;
