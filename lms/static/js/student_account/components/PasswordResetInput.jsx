/* globals gettext */

import PropTypes from 'prop-types';
import React from 'react';

import { Form } from '@openedx/paragon';

function PasswordResetInput(props) {
    return (
        <div className="form-field">
            <Form.Control
                id={props.name}
                type="password"
                isInvalid={props.themes && props.themes.includes('danger')}
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
