import React from 'react';
import PropTypes from 'prop-types';
import { Button, InputText, StatusAlert, InputSelect } from '@edx/paragon';

export const ProgramEnrollmentsInspectorPage = props => (
  <form method="get">
    {props.errors.map(errorItem => (
      <StatusAlert
        open
        dismissible={false}
        alertType="danger"
        dialog={errorItem}
      />
    ))}
    <div key="edX_accounts">
      <InputText
        name="edx_user"
        label="edX account username or email"
        value={(props.learnerInfo && props.learnerInfo.user && props.learnerInfo.user.username) || ''}
      />
    </div>
    <div key="school_accounts">
      <InputSelect
        name="IdPSelect"
        label="Learner Account Providers"
        value="Select One"
        options={
          props.orgKeys
        }
      />

      <InputText
        name="external_user_key"
        label="Institution user key from school. For example, GTPersonDirectoryId for GT students"
        value={(props.learnerInfo && props.learnerInfo.user && props.learnerInfo.user.external_user_key) || ''}
      />
    </div>
    <Button label="Search" type="submit" className={['btn', 'btn-primary']} />
  </form>
);

ProgramEnrollmentsInspectorPage.propTypes = {
  errors: PropTypes.arrayOf(PropTypes.string),
  learnerInfo: PropTypes.shape({
    user: PropTypes.shape({
      external_user_key: PropTypes.string,
      username: PropTypes.string,
    }),
    enrollments: PropTypes.arrayOf(
      PropTypes.string,
    ),
  }),
  orgKeys: PropTypes.arrayOf(PropTypes.object),
};

ProgramEnrollmentsInspectorPage.defaultProps = {
  errors: [],
  learnerInfo: {},
  orgKeys: [],
};
