import React from 'react';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import { Button, InputText, TextArea, StatusAlert } from '@edx/paragon';

export const LinkProgramEnrollmentsSupportPage = props => (
  <form method="post">
    <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
    {props.successes.length > 0 && (
      <StatusAlert
        open
        alertType="success"
        dialog={(
          <div>
            <span>There were { props.successes.length } successful linkages</span>
          </div>
        )}
      />
    )}
    {props.errors.map(errorItem => (
      <StatusAlert
        open
        dismissible={false}
        alertType="danger"
        dialog={errorItem}
      />
    ))}
    <InputText
      name="program_uuid"
      label="Program UUID"
      value={props.programUUID}
    />
    <TextArea
      name="text"
      label="List of external_user_key, lms_username, one per line"
      value={props.text}
      placeholder="external_student_key,lms_username"
    />
    <Button label="Submit" type="submit" className={['btn', 'btn-primary']} />
  </form>
);

LinkProgramEnrollmentsSupportPage.propTypes = {
  successes: PropTypes.arrayOf(PropTypes.string),
  errors: PropTypes.arrayOf(PropTypes.string),
  programUUID: PropTypes.string,
  text: PropTypes.string,
};

LinkProgramEnrollmentsSupportPage.defaultProps = {
  successes: [],
  errors: [],
  programUUID: '',
  text: '',
};
