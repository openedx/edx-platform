import React from 'react';
import get from 'lodash/get';
import Wizard from './Wizard';
import Cookies from 'js-cookie';
import { SelectWithInput } from './SelectWithInput'
import { MultiselectDropdown } from './MultiselectDropdown';
import AxiosJwtTokenService from '../jwt_auth/AxiosJwtTokenService';


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
      error: false,
      errorMessage: '',
      loading: true,
      open: this.props.open,
      selected: Object.values(FIELD_NAMES).reduce((acc, current) => ({ ...acc, [current]: '' }), {}),
    };
    this.handleSelectChange = this.handleSelectChange.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.loadOptions = this.loadOptions.bind(this);

    // Get JWT token service to ensure the JWT token refreshes if needed
    const accessToken = this.props.jwtAuthToken;
    const refreshUrl = `${this.props.lmsRootUrl}/login_refresh`;
    this.jwtTokenService = new AxiosJwtTokenService(
      accessToken,
      refreshUrl,
    );
  }

  async componentDidMount() {
    const requestOptions = {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFTOKEN': Cookies.get('demographics_csrftoken'),
        'USE-JWT-COOKIE': true
      },
    };
    let options = {};
    let optionsResponse = {};
    let response = {};
    let data = {};

    // gather options for the demographics selects
    try {
      optionsResponse = await fetch(`${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/`, { method: 'OPTIONS' })
      // this should only fail if demographics is down
      if (optionsResponse.status !== 200) {
        let error = await optionsResponse.json().detail;
        throw error;
      }
      options = await optionsResponse.json();
    } catch (error) {
      //TODO: Possibly create an error message here to expose to the user
      console.log(error)
      this.setState({ loading: false, error: true, errorMessage: error });
    }

    // gather previously answers questions
    try {
      await this.jwtTokenService.getJwtToken();
      response = await fetch(`${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/${this.props.user}/`, requestOptions);
      // if the user has not yet bee created in the demographics service, we need to make a post to create an entry
      if (response.status !== 200) {
        // we get a 404 if the user resource does not exist in demographics, which is expected.
        if (response.status === 404) {
          try {
            requestOptions.method = 'POST'
            requestOptions.body = JSON.stringify({
              user: this.props.user,
            });
            response = await fetch(`${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/`, requestOptions);
            // A 201 is a created success message. if we don't get a 201, throw an error.
            if(response.status !== 201) {
              const error = await response.json();
              throw error.detail;
            }
          } catch(error) {
            this.setState({ loading: false, error: true, errorMessage: error });
          }
        } else {
          const error = await response.json();
          throw error.detail;
        }
      }

      data = await response.json();
      if (data[FIELD_NAMES.ETHNICITY]) {
        // map ethnicity data to match what the UI requires
        data[FIELD_NAMES.ETHNICITY] = this.reduceEthnicityArray(data[FIELD_NAMES.ETHNICITY]);
      }
      this.setState({ options: options.actions.POST, loading: false, selected: data });
    } catch (error) {
      this.setState({ loading: false, error: true, errorMessage: error });
    }
    // we add a class here to prevent scrolling on anything that is not the modal
    document.body.classList.add('modal-open');
  }

  componentWillUnmount() {
    document.body.classList.remove('modal-open');
  }

  loadOptions(field) {
    const { choices } = get(this.state.options, field, { choices: [] });
    if (choices.length) {
      return choices.map(choice => <option value={choice.value} key={choice.value}>{choice.display_name}</option>);
    }
  }

  async handleSelectChange(e) {
    const name = e.target.name;
    const value = e.target.value;
    const options = {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFTOKEN': Cookies.get('demographics_csrftoken'),
        'USE-JWT-COOKIE': true
      },
      body: JSON.stringify({
        [name]: value,
      }),
    };

    try {
      await this.jwtTokenService.getJwtToken();
      await fetch(`${this.props.demographicsBaseUrl}/demographics/api/v1/demographics/${this.props.user}/`, options)
    } catch (error) {
      this.setState({ loading: false, error: true, errorMessage: error });
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


  render() {
    if (this.state.loading) {
      console.log("loading")
      return <div className="demographics-collection-modal d-flex justify-content-center align-items-start" />
    }

    console.log('something', this.state.error)
    return (
      <div className="demographics-collection-modal d-flex justify-content-center align-items-start">
        <Wizard
          onWizardComplete={this.props.closeModal}
          wizardContext={{ ...this.state.selected, options: this.state.options }}
          error={this.state.error}
        >
          <Wizard.Header>
            {({ currentPage, totalPages }) => (
              <div>
                <h2>Help make edX better for everyone!</h2>
                <p>Thanks for registering with edX! Before getting started, please complete the additional information below to help your fellow learners. Your information will never be sold.</p>
                <br />
                <span className="fa-info-circle" />
                <a className="pl-3">Why does edX collect this information?</a>
                <br />
                <p>Part {currentPage} of {totalPages}</p>
              </div>
            )}
          </Wizard.Header>
          <Wizard.Page>
            {({ wizardConsumer }) =>
              <div className="demographics-form-container">
                <SelectWithInput
                  selectName={FIELD_NAMES.GENDER}
                  selectId={FIELD_NAMES.GENDER}
                  selectValue={wizardConsumer[FIELD_NAMES.GENDER]}
                  selectOnChange={this.handleSelectChange}
                  labelText={"Gender identity"}
                  options={[
                    <option value="default" key="default">Select gender</option>,
                    this.loadOptions(FIELD_NAMES.GENDER)
                  ]}
                  showInput={wizardConsumer[FIELD_NAMES.GENDER] == "self-describe"}
                  inputName={FIELD_NAMES.GENDER_DESCRIPTION}
                  inputId={FIELD_NAMES.GENDER_DESCRIPTION}
                  inputType="text"
                  inputValue={wizardConsumer[FIELD_NAMES.GENDER_DESCRIPTION]}
                  inputOnChange={this.handleInputChange}
                  inputOnBlur={this.handleSelectChange}

                />
                <MultiselectDropdown
                  label="Which of the following describes you best?"
                  emptyLabel="Check all that apply"
                  options={get(this.state.options, FIELD_NAMES.ETHNICITY_OPTIONS, { choices: [] }).choices}
                  selected={wizardConsumer[FIELD_NAMES.ETHNICITY]}
                  onChange={(values) => {
                    const filteredValues = values.filter(i => i !== 'declined');
                    this.setState(prevState => ({ selected: { ...prevState.selected, [FIELD_NAMES.ETHNICITY]: filteredValues } }));
                  }}
                  onBlur={() => {
                    const e = {
                      target: {
                        name: FIELD_NAMES.ETHNICITY,
                        value: wizardConsumer[FIELD_NAMES.ETHNICITY].map(ethnicity => ({ ethnicity, value: ethnicity })),
                      }
                    }
                    this.handleSelectChange(e);
                  }}
                />
                <label htmlFor={FIELD_NAMES.INCOME}>Household income</label>
                <select
                  onChange={this.handleSelectChange}
                  className="form-control"
                  name={FIELD_NAMES.INCOME} id={FIELD_NAMES.INCOME}
                  value={wizardConsumer[FIELD_NAMES.INCOME]}
                >
                  <option value="default">Select income</option>
                  {
                    this.loadOptions(FIELD_NAMES.INCOME)
                  }
                </select>
              </div>
            }
          </Wizard.Page>
          <Wizard.Page>
            {({ wizardConsumer }) =>
              <div className="demographics-form-container">
                <label htmlFor={FIELD_NAMES.MILITARY}>Have you ever served on active duty in the U.S. Armed Forces, Reserves, or National Guard?</label>
                <select
                  className="form-control"
                  onChange={this.handleSelectChange}
                  name={FIELD_NAMES.MILITARY}
                  id={FIELD_NAMES.MILITARY}
                  value={wizardConsumer[FIELD_NAMES.MILITARY]}
                >
                  <option value="default">Select service branch</option>
                  {
                    this.loadOptions(FIELD_NAMES.MILITARY)
                  }
                </select>
              </div>
            }
          </Wizard.Page>
          <Wizard.Page>
            {({ wizardConsumer }) =>
              <div className="demographics-form-container">
                <label htmlFor={FIELD_NAMES.EDUCATION_LEVEL}>Your highest level of education</label>
                <select
                  className="form-control"
                  onChange={this.handleSelectChange}
                  name={FIELD_NAMES.EDUCATION_LEVEL}
                  id={FIELD_NAMES.EDUCATION_LEVEL}
                  value={wizardConsumer[FIELD_NAMES.EDUCATION_LEVEL]}
                >
                  <option>Select level of education</option>
                  {
                    this.loadOptions(FIELD_NAMES.EDUCATION_LEVEL)
                  }
                </select>
                <label htmlFor={FIELD_NAMES.PARENT_EDUCATION}>What is the highest level of education that any of your parents or guardians have achieved?</label>
                <select
                  className="form-control"
                  onChange={this.handleSelectChange}
                  name={FIELD_NAMES.PARENT_EDUCATION}
                  id={FIELD_NAMES.PARENT_EDUCATION}
                  value={wizardConsumer[FIELD_NAMES.PARENT_EDUCATION]}
                >
                  <option value="default">Select guardian education</option>
                  {
                    this.loadOptions(FIELD_NAMES.PARENT_EDUCATION)
                  }
                </select>
              </div>
            }
          </Wizard.Page>
          <Wizard.Page>
            {({ wizardConsumer }) =>
              <div className="demographics-form-container">
                <SelectWithInput
                  selectName={FIELD_NAMES.WORK_STATUS}
                  selectId={FIELD_NAMES.WORK_STATUS}
                  selectValue={wizardConsumer[FIELD_NAMES.WORK_STATUS]}
                  selectOnChange={this.handleSelectChange}
                  labelText={"Employment status"}
                  options={[
                    this.loadOptions(FIELD_NAMES.WORK_STATUS)
                  ]}
                  showInput={wizardConsumer[FIELD_NAMES.WORK_STATUS] == "other"}
                  inputName={FIELD_NAMES.WORK_STATUS_DESCRIPTION}
                  inputId={FIELD_NAMES.WORK_STATUS_DESCRIPTION}
                  inputType="text"
                  inputValue={wizardConsumer[FIELD_NAMES.WORK_STATUS_DESCRIPTION]}
                  inputOnChange={this.handleInputChange}
                  inputOnBlur={this.handleSelectChange}

                />
                <label htmlFor={FIELD_NAMES.CURRENT_WORK}>What industry do you currently work in?</label>
                <select
                  className="form-control"
                  onChange={this.handleSelectChange}
                  name={FIELD_NAMES.CURRENT_WORK}
                  id={FIELD_NAMES.CURRENT_WORK}
                  value={wizardConsumer[FIELD_NAMES.CURRENT_WORK]}
                >
                  <option value="default">Select current industry</option>
                  {
                    this.loadOptions(FIELD_NAMES.CURRENT_WORK)
                  }
                </select>
                <label htmlFor={FIELD_NAMES.FUTURE_WORK}>What industry do you want to work in</label>
                <select
                  className="form-control"
                  onChange={this.handleSelectChange}
                  name={FIELD_NAMES.FUTURE_WORK}
                  id={FIELD_NAMES.FUTURE_WORK}
                  value={wizardConsumer[FIELD_NAMES.FUTURE_WORK]}
                >
                  <option value="default">Select prospective industry</option>
                  {
                    this.loadOptions(FIELD_NAMES.FUTURE_WORK)
                  }
                </select>
              </div>
            }
          </Wizard.Page>
          <Wizard.Closer>
            <h3>Thank you! You’re helping make edX better for everyone.</h3>
          </Wizard.Closer>
          <Wizard.ErrorPage>
            <div>
              {this.state.error.length ? this.state.error : "something went wrong"}
            </div>
          </Wizard.ErrorPage>
        </Wizard>
      </div>
    )
  }
}

export { DemographicsCollectionModal };
