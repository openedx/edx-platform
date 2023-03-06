/* global gettext */
import React from 'react';
import get from 'lodash/get';
import Wizard from './Wizard';
import Cookies from 'js-cookie';
import { SelectWithInput } from './SelectWithInput'
import { MultiselectDropdown } from './MultiselectDropdown';
import AxiosJwtTokenService from '../jwt_auth/AxiosJwtTokenService';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';
import AxiosCsrfTokenService from '../jwt_auth/AxiosCsrfTokenService';
import FocusLock from 'react-focus-lock';

const FIELD_NAMES = {
    CURRENT_WORK: "current_work_sector",
    FUTURE_WORK: "future_work_sector",
    GENDER: "gender",
    GENDER_DESCRIPTION: "gender_description",
    INCOME: "income",
    EDUCATION_LEVEL: "learner_education_level",
    MILITARY: "military_history",
    PARENT_EDUCATION: "parent_education_level",
    // For some reason, ethnicity has the really long property chain to get to the choices
    ETHNICITY_OPTIONS: "user_ethnicity.child.children.ethnicity",
    ETHNICITY: "user_ethnicity",
    WORK_STATUS: "work_status",
    WORK_STATUS_DESCRIPTION: "work_status_description",
};


class DemographicsCollectionModal extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            options: {},
            // a general error something goes really wrong
            error: false,
            // an error for when a specific demographics question fails to save
            fieldError: false,
            errorMessage: '',
            loading: true,
            open: this.props.open,
            selected: {
                [FIELD_NAMES.CURRENT_WORK]: '',
                [FIELD_NAMES.FUTURE_WORK]: '',
                [FIELD_NAMES.GENDER]: '',
                [FIELD_NAMES.GENDER_DESCRIPTION]: '',
                [FIELD_NAMES.INCOME]: '',
                [FIELD_NAMES.EDUCATION_LEVEL]: '',
                [FIELD_NAMES.MILITARY]: '',
                [FIELD_NAMES.PARENT_EDUCATION]: '',
                [FIELD_NAMES.ETHNICITY]: [],
                [FIELD_NAMES.WORK_STATUS]: '',
                [FIELD_NAMES.WORK_STATUS_DESCRIPTION]: '',
            }
        };
        this.handleSelectChange = this.handleSelectChange.bind(this);
        this.handleMultiselectChange = this.handleMultiselectChange.bind(this);
        this.handleInputChange = this.handleInputChange.bind(this);
        this.loadOptions = this.loadOptions.bind(this);
        this.getDemographicsQuestionOptions = this.getDemographicsQuestionOptions.bind(this);
        this.getDemographicsData = this.getDemographicsData.bind(this);

        // Get JWT token service to ensure the JWT token refreshes if needed
        const accessToken = this.props.jwtAuthToken;
        const refreshUrl = `${this.props.lmsRootUrl}/login_refresh`;
        this.jwtTokenService = new AxiosJwtTokenService(
            accessToken,
            refreshUrl,
        );
        this.csrfTokenService = new AxiosCsrfTokenService(this.props.csrfTokenPath)
    }

    async componentDidMount() {
    // we add a class here to prevent scrolling on anything that is not the modal
        document.body.classList.add('modal-open');
        const options = await this.getDemographicsQuestionOptions();
        // gather previously answers questions
        const data = await this.getDemographicsData();
        this.setState({ options: options.actions.POST, loading: false, selected: data });
    }

    componentWillUnmount() {
    // remove the class to allow the dashboard content to scroll
        document.body.classList.remove('modal-open');
    }

    loadOptions(field) {
        const { choices } = get(this.state.options, field, { choices: [] });
        if (choices.length) {
            return choices.map((choice, i) => <option value={choice.value} key={choice.value + i}>{choice.display_name}</option>);
        }
    }

    async handleSelectChange(e) {
        const url = `${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/${this.props.user}/`;
        const name = e.target.name;
        const value = e.target.value;
        const options = {
            method: 'PATCH',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'USE-JWT-COOKIE': true,
                'X-CSRFToken': await this.retrieveDemographicsCsrfToken(url),
            },
            body: JSON.stringify({
                [name]: value === "default" ? null : value,
            }),
        };
        try {
            await this.jwtTokenService.getJwtToken();
            await fetch(url, options)
        } catch (error) {
            this.setState({ loading: false, fieldError: true, errorMessage: error });
        }

        if (name === 'user_ethnicity') {
            return this.reduceEthnicityArray(value);
        }
        this.setState(prevState => ({
            selected: {
                ...prevState.selected,
                [name]: value,
            }
        }));
    }

    handleMultiselectChange(values) {
        const decline = values.find(i => i === 'declined');
        this.setState(({ selected }) => {
            // decline was previously selected
            if (selected[FIELD_NAMES.ETHNICITY].find(i => i === 'declined')) {
                return { selected: { ...selected, [FIELD_NAMES.ETHNICITY]: values.filter(value => value !== 'declined') } }
                // decline was just selected
            } else if (decline) {
                return { selected: { ...selected, [FIELD_NAMES.ETHNICITY]: [decline] } }
                // anything else was selected
            } else {
                return { selected: { ...selected, [FIELD_NAMES.ETHNICITY]: values } }
            }
        });
    }

    handleInputChange(e) {
        const name = e.target.name;
        const value = e.target.value;
        this.setState(prevState => ({
            selected: {
                ...prevState.selected,
                [name]: value,
            }
        }));
    }

    // We need to transform the ethnicity array before we POST or after GET the data to match
    // from [{ethnicity: 'example}] => to ['example']
    // the format the UI requires the data to be in.
    reduceEthnicityArray(ethnicityArray) {
        return ethnicityArray.map((o) => o.ethnicity);
    }

    // Sets the CSRF token cookie to be used before each request that needs it.
    // if the cookie is already set, return it instead. We don't have to worry
    // about the cookie expiring, as it is tied to the session.
    async retrieveDemographicsCsrfToken(url) {
        let csrfToken = Cookies.get('demographics_csrftoken');
        if (!csrfToken) {
            // set the csrf token cookie if not already set
            csrfToken = await this.csrfTokenService.getCsrfToken(url);
            Cookies.set('demographics_csrftoken', csrfToken);
        }
        return csrfToken;
    }

    // We gather the possible answers to any demographics questions from the OPTIONS of the api
    async getDemographicsQuestionOptions() {
        try {
            const optionsResponse = await fetch(`${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/`, { method: 'OPTIONS' })
            const demographicsOptions = await optionsResponse.json();
            return demographicsOptions;
        } catch (error) {
            this.setState({ loading: false, error: true, errorMessage: error });
        }
    }

    async getDemographicsData() {
        const requestOptions = {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'USE-JWT-COOKIE': true
            },
        };
        let response;
        let data;
        try {
            await this.jwtTokenService.getJwtToken();
            response = await fetch(`${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/${this.props.user}/`, requestOptions);
        } catch (e) {
            // an error other than "no entry found" occured
            this.setState({ loading: false, error: true, errorMessage: e });
        }
        // an entry was not found in demographics, so we need to create one
        if (response.status === 404) {
            data = await this.createDemographicsEntry();
            return data;
        }
        // Otherwise, just return the data found
        data = await response.json();
        if (data[FIELD_NAMES.ETHNICITY]) {
            // map ethnicity data to match what the UI requires
            data[FIELD_NAMES.ETHNICITY] = this.reduceEthnicityArray(data[FIELD_NAMES.ETHNICITY]);
        }
        return data;
    }

    async createDemographicsEntry() {
        const postUrl = `${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/`;
        const postOptions = {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'USE-JWT-COOKIE': true,
                'X-CSRFToken': await this.retrieveDemographicsCsrfToken(postUrl),
            },
            body: JSON.stringify({
                user: this.props.user,
            }),
        };
        // Create the entry for the user
        try {
            const postResponse = await fetch(postUrl, postOptions);
            const data = await postResponse.json();
            return data;
        } catch (e) {
            this.setState({ loading: false, error: true, errorMessage: e });
        }
    }

    render() {
        if (this.state.loading) {
            return <div className="demographics-collection-modal d-flex justify-content-center align-items-start" />
        }
        return (
            <FocusLock>
                <div className="demographics-collection-modal d-flex justify-content-center align-items-start">
                    <Wizard
                        onWizardComplete={this.props.closeModal}
                        dismissBanner={this.props.dismissBanner}
                        wizardContext={{ ...this.state.selected, options: this.state.options }}
                        error={this.state.error}
                    >
                        <Wizard.Header>
                            {({ currentPage, totalPages }) => (
                                <div>
                                    <p className="font-weight-light">
                                        {StringUtils.interpolate(
                                            gettext('Section {currentPage} of {totalPages}'),
                                            {
                                                currentPage: currentPage,
                                                totalPages: totalPages
                                            }
                                        )
                                        }
                                    </p>
                                    <h2 className="mb-1 mt-4 font-weight-bold text-secondary">
                                        {gettext('Help make edX better for everyone!')}
                                    </h2>
                                    <p className="message">
                                        {gettext('Welcome to edX! Before you get started, please take a few minutes to fill-in the additional information below to help us understand a bit more about your background. You can always edit this information later in Account Settings.')}
                                    </p>
                                    <br />
                                    <span aria-hidden="true" className="fa fa-info-circle" />
                                    {/* Need to strip out extra '"' characters in the marketingSiteBaseUrl prop or it tries to setup the href as a relative URL */}
                                    <a className="pl-3" target="_blank" rel="noopener" href={`${this.props.marketingSiteBaseUrl}/demographics`.replace(/"/g, "")}>
                                        {gettext('Why does edX collect this information?')}
                                    </a>
                                    <br />
                                    {this.state.fieldError && <p className="field-error">{gettext("An error occurred while attempting to retrieve or save the information below. Please try again later.")}</p>}
                                </div>
                            )}
                        </Wizard.Header>
                        <Wizard.Page>
                            {({ wizardConsumer }) =>
                                <div className="demographics-form-container" data-hj-suppress>
                                    {/* Gender Identity */}
                                    <SelectWithInput
                                        selectName={FIELD_NAMES.GENDER}
                                        selectId={FIELD_NAMES.GENDER}
                                        selectValue={wizardConsumer[FIELD_NAMES.GENDER]}
                                        selectOnChange={this.handleSelectChange}
                                        labelText={gettext("What is your gender identity?")}
                                        options={[
                                            <option value="default" key="default">{gettext("Select gender")}</option>,
                                            this.loadOptions(FIELD_NAMES.GENDER)
                                        ]}
                                        showInput={wizardConsumer[FIELD_NAMES.GENDER] == "self-describe"}
                                        inputName={FIELD_NAMES.GENDER_DESCRIPTION}
                                        inputId={FIELD_NAMES.GENDER_DESCRIPTION}
                                        inputType="text"
                                        inputValue={wizardConsumer[FIELD_NAMES.GENDER_DESCRIPTION]}
                                        inputOnChange={this.handleInputChange}
                                        inputOnBlur={this.handleSelectChange}
                                        disabled={this.state.fieldError}
                                    />
                                    {/* Ethnicity */}
                                    <MultiselectDropdown
                                        label={gettext("Which of the following describes you best?")}
                                        emptyLabel={gettext("Check all that apply")}
                                        options={get(this.state.options, FIELD_NAMES.ETHNICITY_OPTIONS, { choices: [] }).choices}
                                        selected={wizardConsumer[FIELD_NAMES.ETHNICITY]}
                                        onChange={this.handleMultiselectChange}
                                        disabled={this.state.fieldError}
                                        onBlur={() => {
                                            // we create a fake "event", and then use it to call our normal selection handler function that
                                            // is used by the other dropdowns.
                                            const e = {
                                                target: {
                                                    name: FIELD_NAMES.ETHNICITY,
                                                    value: wizardConsumer[FIELD_NAMES.ETHNICITY].map(ethnicity => ({ ethnicity, value: ethnicity })),
                                                }
                                            }
                                            this.handleSelectChange(e);
                                        }}
                                    />
                                    {/* Family Income */}
                                    <div className="d-flex flex-column pb-3">
                                        <label htmlFor={FIELD_NAMES.INCOME}>
                                            {gettext("What was the total combined income, during the last 12 months, of all members of your family? ")}
                                        </label>
                                        <select
                                            onChange={this.handleSelectChange}
                                            className="form-control"
                                            name={FIELD_NAMES.INCOME} id={FIELD_NAMES.INCOME}
                                            value={wizardConsumer[FIELD_NAMES.INCOME]}
                                            disabled={this.state.fieldError}
                                        >
                                            <option value="default">{gettext("Select income")}</option>
                                            {
                                                this.loadOptions(FIELD_NAMES.INCOME)
                                            }
                                        </select>
                                    </div>
                                </div>
                            }
                        </Wizard.Page>
                        <Wizard.Page>
                            {({ wizardConsumer }) =>
                                <div className="demographics-form-container" data-hj-suppress>
                                    {/* Military History */}
                                    <div className="d-flex flex-column pb-3">
                                        <label htmlFor={FIELD_NAMES.MILITARY}>
                                            {gettext("Have you ever served on active duty in the U.S. Armed Forces, Reserves, or National Guard?")}
                                        </label>
                                        <select
                                            autoFocus
                                            className="form-control"
                                            onChange={this.handleSelectChange}
                                            name={FIELD_NAMES.MILITARY}
                                            id={FIELD_NAMES.MILITARY}
                                            value={wizardConsumer[FIELD_NAMES.MILITARY]}
                                            disabled={this.state.fieldError}
                                        >
                                            <option value="default">{gettext("Select military status")}</option>
                                            {
                                                this.loadOptions(FIELD_NAMES.MILITARY)
                                            }
                                        </select>
                                    </div>
                                </div>
                            }
                        </Wizard.Page>
                        <Wizard.Page>
                            {({ wizardConsumer }) =>
                                <div className="demographics-form-container" data-hj-suppress>
                                    {/* Learner Education Level */}
                                    <div className="d-flex flex-column pb-3">
                                        <label htmlFor={FIELD_NAMES.EDUCATION_LEVEL}>
                                            {gettext("What is the highest level of education that you have achieved so far?")}
                                        </label>
                                        <select
                                            className="form-control"
                                            autoFocus
                                            onChange={this.handleSelectChange}
                                            key="self-education"
                                            name={FIELD_NAMES.EDUCATION_LEVEL}
                                            id={FIELD_NAMES.EDUCATION_LEVEL}
                                            value={wizardConsumer[FIELD_NAMES.EDUCATION_LEVEL]}
                                            disabled={this.state.fieldError}
                                        >
                                            <option value="default">{gettext("Select level of education")}</option>
                                            {
                                                this.loadOptions(FIELD_NAMES.EDUCATION_LEVEL)
                                            }
                                        </select>
                                    </div>
                                    {/* Parent/Guardian Education Level */}
                                    <div className="d-flex flex-column pb-3">
                                        <label htmlFor={FIELD_NAMES.PARENT_EDUCATION}>
                                            {gettext("What is the highest level of education that any of your parents or guardians have achieved?")}
                                        </label>
                                        <select
                                            className="form-control"
                                            onChange={this.handleSelectChange}
                                            name={FIELD_NAMES.PARENT_EDUCATION}
                                            id={FIELD_NAMES.PARENT_EDUCATION}
                                            value={wizardConsumer[FIELD_NAMES.PARENT_EDUCATION]}
                                            disabled={this.state.fieldError}
                                        >
                                            <option value="default">{gettext("Select guardian education")}</option>
                                            {
                                                this.loadOptions(FIELD_NAMES.PARENT_EDUCATION)
                                            }
                                        </select>
                                    </div>
                                </div>
                            }
                        </Wizard.Page>
                        <Wizard.Page>
                            {({ wizardConsumer }) =>
                                <div className="demographics-form-container" data-hj-suppress>
                                    {/* Employment Status */}
                                    <SelectWithInput
                                        selectName={FIELD_NAMES.WORK_STATUS}
                                        selectId={FIELD_NAMES.WORK_STATUS}
                                        selectValue={wizardConsumer[FIELD_NAMES.WORK_STATUS]}
                                        selectOnChange={this.handleSelectChange}
                                        labelText={"What is your current employment status?"}
                                        options={[
                                            <option value="default" key="default">{gettext("Select employment status")}</option>,
                                            this.loadOptions(FIELD_NAMES.WORK_STATUS)
                                        ]}
                                        showInput={wizardConsumer[FIELD_NAMES.WORK_STATUS] == "other"}
                                        inputName={FIELD_NAMES.WORK_STATUS_DESCRIPTION}
                                        inputId={FIELD_NAMES.WORK_STATUS_DESCRIPTION}
                                        inputType="text"
                                        inputValue={wizardConsumer[FIELD_NAMES.WORK_STATUS_DESCRIPTION]}
                                        inputOnChange={this.handleInputChange}
                                        inputOnBlur={this.handleSelectChange}
                                        disabled={this.state.fieldError}
                                    />
                                    {/* Current Work Industry */}
                                    <div className="d-flex flex-column pb-3">
                                        <label htmlFor={FIELD_NAMES.CURRENT_WORK}>
                                            {gettext("What industry do you currently work in?")}
                                        </label>
                                        <select
                                            className="form-control"
                                            onChange={this.handleSelectChange}
                                            name={FIELD_NAMES.CURRENT_WORK}
                                            id={FIELD_NAMES.CURRENT_WORK}
                                            value={wizardConsumer[FIELD_NAMES.CURRENT_WORK]}
                                            disabled={this.state.fieldError}
                                        >
                                            <option value="default">{gettext("Select current industry")}</option>
                                            {
                                                this.loadOptions(FIELD_NAMES.CURRENT_WORK)
                                            }
                                        </select>
                                    </div>
                                    {/* Future Work Industry */}
                                    <div className="d-flex flex-column pb-3">
                                        <label htmlFor={FIELD_NAMES.FUTURE_WORK}>
                                            {gettext("What industry do you want to work in?")}
                                        </label>
                                        <select
                                            className="form-control"
                                            onChange={this.handleSelectChange}
                                            name={FIELD_NAMES.FUTURE_WORK}
                                            id={FIELD_NAMES.FUTURE_WORK}
                                            value={wizardConsumer[FIELD_NAMES.FUTURE_WORK]}
                                            disabled={this.state.fieldError}
                                        >
                                            <option value="default">{gettext("Select prospective industry")}</option>
                                            {
                                                this.loadOptions(FIELD_NAMES.FUTURE_WORK)
                                            }
                                        </select>
                                    </div>
                                </div>
                            }
                        </Wizard.Page>
                        <Wizard.Closer>
                            <div className="demographics-modal-closer m-sm-0">
                                <i className="fa fa-check" aria-hidden="true"></i>
                                <h3>
                                    {gettext("Thank you! You’re helping make edX better for everyone.")}
                                </h3>
                            </div>
                        </Wizard.Closer>
                        <Wizard.ErrorPage>
                            <div>
                                {this.state.error.length ? this.state.error : gettext("An error occurred while attempting to retrieve or save the information below. Please try again later.")}
                            </div>
                        </Wizard.ErrorPage>
                    </Wizard>
                </div>
            </FocusLock>
        )
    }
}

export { DemographicsCollectionModal };
