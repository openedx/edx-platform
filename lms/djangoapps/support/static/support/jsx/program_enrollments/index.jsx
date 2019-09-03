import React from 'react';
import Cookies from 'js-cookie';
import { Button, InputText, TextArea, StatusAlert, Collapsible, Dropdown } from '@edx/paragon';

export const LinkProgramEnrollmentsSupportPage = props => (
  <form method="post">
    <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')}/>
    {props.successes.length > 0 && (
      <StatusAlert
        open
        alertType='success'
        dialog={(
          <div>
            <span>There were { props.successes.length } successful linkages</span>
          </div>
        )}
      />
    )}
    {props.errors.map(error_item => (
      <StatusAlert
        open
        dismissible={false}
        alertType='danger'
        dialog={error_item}
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
    <Button label="Submit" type='submit' className={['btn', 'btn-primary']}/>
  </form>
);