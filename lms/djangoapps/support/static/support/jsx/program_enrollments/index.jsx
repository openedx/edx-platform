import React from 'react';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import {
    Button, Form, Alert,
} from '@openedx/paragon';

// eslint-disable-next-line react/function-component-definition
export const LinkProgramEnrollmentsSupportPage = props => (
    <form method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
        {props.successes.length > 0 && (
            <Alert
                show
                variant="success"
            >
                <div>
                    <span>There were { props.successes.length } successful linkages</span>
                </div>
            </Alert>
        )}
        {props.errors.map(errorItem => (
            <Alert
                show
                dismissible={false}
                variant="danger"
                key={errorItem}
            >
                {errorItem}
            </Alert>
        ))}
        <Form.Group>
            <Form.Label>Program UUID</Form.Label>
            <Form.Control
                name="program_uuid"
                value={props.programUUID}
            />
        </Form.Group>
        <Form.Group>
            <Form.Label>List of external_user_key, lms_username, one per line</Form.Label>
            <Form.Control
                as="textarea"
                name="text"
                value={props.text}
                placeholder="external_student_key,lms_username"
            />
        </Form.Group>
        <Button variant="primary" type="submit">Submit</Button>
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
