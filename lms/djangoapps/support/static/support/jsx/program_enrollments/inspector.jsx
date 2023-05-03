import React from 'react';
import PropTypes from 'prop-types';
import { Button, InputText, StatusAlert, InputSelect } from '@edx/paragon';

/*
To improve the UI here, we should move this tool to the support Micro-Frontend.
This work will be groomed and covered by MST-180
*/
const renderUserSection = userObj => (
    <div>
        <h3>edX account Info</h3>
        <div className="ml-5">
            <div><span className="font-weight-bold">Username</span>: {userObj.username}</div>
            <div><span className="font-weight-bold">Email</span>: {userObj.email}</div>
            {userObj.external_user_key && (
                <div>
                    <span className="font-weight-bold">External User Key</span>
          : {userObj.external_user_key}
                </div>
            )}
            {userObj.sso_list ? (
                <div>
                    <h4>List of Single Sign On Records: </h4>
                    <ul>
                        {userObj.sso_list.map(sso => (
                            <li>{sso.uid}</li>
                        ))}
                    </ul>
                </div>
            ) : (
                <div> There is no Single Sign On record associated with this user!</div>
            )}
        </div>
        <hr />
    </div>
);


const renderVerificationSection = verificationStatus => (
    <div>
        <h3>ID Verification</h3>
        <div className="ml-5">
            <div><span className="font-weight-bold">Status</span>: {verificationStatus.status}</div>
            {verificationStatus.error && (
                <div>
                    <span className="font-weight-bold">Verification Error</span>: {verificationStatus.error}
                </div>
            )}
            {verificationStatus.verification_expiry && (
                <div>
                    <span className="font-weight-bold">Verification Expiration Date</span>
          : {verificationStatus.verification_expiry}
                </div>
            )}
        </div>
        <hr />
    </div>
);

const renderEnrollmentsSection = enrollments => (
    <div>
        <h3>Program Enrollments</h3>
        {enrollments.map(enrollment => (
            <div key={enrollment.program_uuid} className="ml-5">
                <h4>
                    <span className="font-weight-bold">
                        {enrollment.program_name}
                    </span> Program ( <span className="font-weight-bold">
                        {enrollment.program_uuid}
                    </span>)
                </h4>
                <div> <span className="font-weight-bold">Status</span>: {enrollment.status} </div>
                <div> <span className="font-weight-bold">Created</span>: {enrollment.created} </div>
                <div> <span className="font-weight-bold">Last updated</span>: {enrollment.modified} </div>
                <div>
                    <span className="font-weight-bold">External User Key</span>
          : {enrollment.external_user_key}
                </div>
                {enrollment.program_course_enrollments && enrollment.program_course_enrollments.map(
                    programCourseEnrollment => (
                        <div key={programCourseEnrollment.course_key} className="ml-5">
                            <h4>
                                <a href={programCourseEnrollment.course_url}>
                                    {programCourseEnrollment.course_key}
                                </a>
                            </h4>
                            <div>
                                <span className="font-weight-bold">Status</span>
                : {programCourseEnrollment.status}
                            </div>
                            <div>
                                <span className="font-weight-bold">Created</span>
                : {programCourseEnrollment.created}
                            </div>
                            <div>
                                <span className="font-weight-bold">Last updated</span>
                : {programCourseEnrollment.modified}
                            </div>
                            {programCourseEnrollment.course_enrollment && (
                                <div className="ml-5">
                                    <h4>Linked course enrollment</h4>
                                    <div><span className="font-weight-bold">Course ID</span>
                    : {programCourseEnrollment.course_enrollment.course_id}
                                    </div>
                                    <div> <span className="font-weight-bold">Is Active</span>
                    : {String(programCourseEnrollment.course_enrollment.is_active)}
                                    </div>
                                    <div> <span className="font-weight-bold">Mode / Track</span>
                    : {programCourseEnrollment.course_enrollment.mode}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
            </div>
        ))}
        <hr />
    </div>
);

const validateInputs = () => {
    const inputEdxUser = self.document.getElementById('edx_user');
    const inputExternalKey = self.document.getElementById('external_key');
    const inputAlert = self.document.getElementById('input_alert');
    if (inputEdxUser.value && inputExternalKey.value) {
        inputAlert.removeAttribute('hidden');
        self.button.disabled = true;
    } else {
        inputAlert.setAttribute('hidden', '');
        self.button.disabled = false;
    }
};

export const ProgramEnrollmentsInspectorPage = props => (
    <div>
        {JSON.stringify(props.learnerInfo) !== '{}' && (<h2> Search Results </h2>)}
        {props.learnerInfo.user &&
      renderUserSection(props.learnerInfo.user)}
        {props.learnerInfo.id_verification &&
      renderVerificationSection(props.learnerInfo.id_verification)}
        {props.learnerInfo.enrollments &&
      renderEnrollmentsSection(props.learnerInfo.enrollments)}
        <form method="get">
            <h2>Search For A Masters Learner Below</h2>
            {props.error && (
                <StatusAlert
                    open
                    dismissible={false}
                    alertType="danger"
                    dialog={props.error}
                />
            )}
            <div id="input_alert" className={'alert alert-danger'} hidden>
        Search either by edx username or email, or Institution user key, but not both
            </div>
            <div key="edX_accounts">
                <InputText
                    id="edx_user"
                    name="edx_user"
                    label="edX account username or email"
                    onChange={validateInputs}
                />
            </div>
            <div key="school_accounts">
                <InputSelect
                    name="org_key"
                    required
                    label="Identity-providing institution"
                    options={
                        props.orgKeys
                    }
                />
                <InputText
                    id="external_key"
                    name="external_user_key"
                    label="Institution user key from school. For example, GTPersonDirectoryId for GT students"
                    onChange={validateInputs}
                />
            </div>
            <Button
                id="search_button"
                label="Search"
                type="submit"
                className={['btn', 'btn-primary']}
                inputRef={(input) => { self.button = input; }}
            />
        </form>
    </div>
);

ProgramEnrollmentsInspectorPage.propTypes = {
    error: PropTypes.string,
    learnerInfo: PropTypes.shape({
        user: PropTypes.shape({
            username: PropTypes.string,
            email: PropTypes.email,
            external_user_key: PropTypes.string,
            sso_list: PropTypes.arrayOf(
                PropTypes.shape({
                    uid: PropTypes.string,
                }),
            ),
        }),
        id_verification: PropTypes.shape({
            status: PropTypes.string,
            error: PropTypes.string,
            verification_expiry: PropTypes.string,
        }),
        enrollments: PropTypes.arrayOf(
            PropTypes.shape({
                created: PropTypes.string,
                modified: PropTypes.string,
                program_uuid: PropTypes.string,
                program_name: PropTypes.string,
                status: PropTypes.string,
                external_user_key: PropTypes.string,
                program_course_enrollments: PropTypes.arrayOf(
                    PropTypes.shape({
                        course_key: PropTypes.string,
                        course_url: PropTypes.string,
                        created: PropTypes.string,
                        modified: PropTypes.string,
                        status: PropTypes.string,
                        course_enrollment: PropTypes.shape({
                            course_id: PropTypes.string,
                            is_active: PropTypes.bool,
                            mode: PropTypes.string,
                        }),
                    })),
            }),
        ),
    }),
    orgKeys: PropTypes.arrayOf(PropTypes.string),
};

ProgramEnrollmentsInspectorPage.defaultProps = {
    error: '',
    learnerInfo: {},
    orgKeys: [],
};
