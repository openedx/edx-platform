/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
