// Changes from Core
// 1. Added span after InputText.
// 2. Updated type of input text.

/* globals gettext */

import PropTypes from 'prop-types';
import React from 'react';

import { InputText } from '@edx/paragon/static';

function PasswordResetInput(props) {
  return (
    <div className="form-field">
      <InputText
        id={props.name}
        type={props.type}
        themes={['danger']}
        dangerIconDescription={gettext('Error: ')}
        required
        {...props}
      />
      <span className='show-pass-icon password-change-eye-icon' onClick={props.onClickHandler}>
          <img src={props.CDN_LINK + 'icons/eye-icon.png'}/>
      </span>
    </div>
  );
}

PasswordResetInput.propTypes = {
  name: PropTypes.string.isRequired,
};

export default PasswordResetInput;
