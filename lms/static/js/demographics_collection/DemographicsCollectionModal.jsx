
import React from 'react';
import get from 'lodash/get';
import Wizard from './Wizard';
import Cookies from 'js-cookie';
import { SelectWithInput } from './SelectWithInput'
import { MultiselectDropdown } from './MultiselectDropdown';


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
}


class DemographicsCollectionModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options: {},
      error: false,
      loading: true,
      open: false,
      selected: Object.values(FIELD_NAMES).reduce((acc, current) => ({ ...acc, [current]: '' }), {}),
    }
    this.handleSelectChange = this.handleSelectChange.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.loadOptions = this.loadOptions.bind(this);
  }

  async componentDidMount() {
    let options = {};
    let optionsResponse = {};
    let response = {};
    let data = {};
    // gather options for the demographics selects
    try {
      optionsResponse = await fetch('http://localhost:18360/demographics/api/v1/demographics/', { method: 'OPTIONS' })
      options = await optionsResponse.json();
    } catch (error) {
      this.setState(error);
    }

    // gather previously answers questions
    try {
      response = await fetch(`http://localhost:18360/demographics/api/v1/demographics/${this.props.user}/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFTOKEN': Cookies.get('demographics_csrftoken'),
          'USE-JWT-COOKIE': true,
        },
      })
      if(response.status !== 200) {
        this.setState({ options: options.actions.POST, loading: false, open: true });
        error = await response.json();
        throw error;
      }
      data = await response.json();
      if(data[FIELD_NAMES.ETHNICITY]) {
        data[FIELD_NAMES.ETHNICITY] = this.reduceEthnicityArray(data[FIELD_NAMES.ETHNICITY]);
      }
      this.setState({ options: options.actions.POST, loading: false, selected: data, open: true });
    } catch (error) {
      this.setState(error)
    }
  }
  
  componentDidUpdate(prevProps, prevState) {
    if(prevState.open !== this.state.open) {
      if(this.state.open) {
        document.body.classList.add('modal-open');
      } else {
        document.body.classList.remove('modal-open');
      }
    }
  }

  loadOptions(field) {
    const { choices } = get(this.state.options, field, { choices: [] });
    if (choices.length) {
      return choices.map(choice => <option value={choice.value} key={choice.value}>{choice.display_name}</option>);
    }
  }
  //TODO: make actual errors
  renderError() {
    <p>Something Went Wrong</p>
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
    }

    try {
      const response = await fetch(`http://localhost:18360/demographics/api/v1/demographics/${this.props.user}/`, options)
    } catch (e) {
      console.log(e);
    }

    if(name === 'user_ethnicity')  {
      return value.reduce((acc, next) => [...acc, next.ethnicity], [])
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
    if (!this.state.open && !this.state.loading) {
      return null;
    }
    console.log(this.state)

    if(this.state.loading) {
      <div className="demographics-collection-modal d-flex justify-content-center align-items-start"/>
    }
    return (
      <div className="demographics-collection-modal d-flex justify-content-center align-items-start">
        {!this.state.loading && !this.state.error &&
          <Wizard 
            onWizardComplete={() => this.setState({ open: false })}
            wizardContext={{ ...this.state.selected, options: this.state.options }}
          >
            <Wizard.Header>
              {({ currentPage, totalPages }) => (
                <div>
                  <h2>Help make edX better for everyone!</h2>
                  <p>Thanks for registering with edX! Before getting started, please complete the additional information below to help your fellow learners. Your information will never be sold.</p>
                  <br/>
                  <span className="fa-info-circle" />
                  <a className="pl-3">Why does edX collect this information?</a>
                  <br/>
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
                      <option value="default">Select gender</option>,
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
          </Wizard>
        }
        {this.state.error && this.renderError()}
      </div>
    )
  }
}

export { DemographicsCollectionModal };
