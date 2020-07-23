
import React, { useState } from 'react';
import get from 'lodash/get';
import { Wizard } from './Wizard';


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
  ETHNICITY: "user_ethnicity.child.children.ethnicity",
  WORK_STATUS: "work_status",
  WORK_STATUS_DESCRIPTION: "work_status_description",
}


class DemographicsCollectionModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options: {},
      loading: true,
      open: true,
      selected: {},
    }
    this.genderRef = null;
    this.loadOptions.bind(this); 
    this.handleSelectChange.bind(this);   
  }

  componentDidMount() {
    fetch('http://localhost:18360/demographics/api/v1/demographics/', {
      method: 'OPTIONS',
      mode: 'cors',
      credentials: 'same-origin',
    })
      .then(response => response.json())
      .then(data => {
        if (data && data.actions) {
          this.setState({ options: data.actions.POST, loading: false })
        }
      })
      console.log(this.genderRef)
  }

  componentDidUpdate() {
    console.log(this.state.selected)
  }

  loadOptions(field) {
    const { choices } = get(this.state.options, field);
    return choices.map(choice => <option value={choice.value} key={choice.value}>{choice.display_name}</option>);
  }

  handleSelectChange(e) {
    
  }

  render() {
    return (
      <div className="demographics-collection-modal">
        {!this.state.loading &&
          <Wizard>
            <Wizard.Header>
              {({ currentPage, totalPages }) => (
                <div>
                  <h1>Help make edX better for everyone!</h1>
                  <p>Thanks for registering with edX! Before getting started, please complete the additional information below to help your fellow learners. Your information will never be sold.</p>
                  <span className="fa-info-circle" /><a>Why does edX collect this information?</a>
                  <p>Part {currentPage} of {totalPages}</p>
                </div>
              )}
            </Wizard.Header>
            <Wizard.Page>
              <div className="demographics-form-container">
                <label htmlFor="genderIdentity">Gender identity</label>
                <select
                name="genderIdentity"
                id="genderIdentity"
                value={this.state.selected.genderIdentity}
                onChange={e => {this.setState({selected: {[e.target.name]: e.target.value}})}}>
                  <option selected>Select gender identity</option>
                  {
                    this.loadOptions(FIELD_NAMES.GENDER)
                  }
                </select>
                <label htmlFor="ethnicBackground">Ethnic background</label>
                <select name="ethnicBackground" id="ethnicBackground">
                  <option selected>Select all that apply</option>
                  {
                    this.loadOptions(FIELD_NAMES.ETHNICITY)
                  }
                </select>
                <label htmlFor="householdIncome">Household income</label>
                <select name="householdIncome" id="householdIncome">
                  <option selected>Select income</option>
                  {
                    this.loadOptions(FIELD_NAMES.INCOME)
                  }
                </select>
              </div>
            </Wizard.Page>
            <Wizard.Page>
              <div className="demographics-form-container">
                <label htmlFor="militaryStatus">Have you ever served on active duty in the U.S. Armed Forces, Reserves, or National Guard?</label>
                <select name="militaryStatus" id="militaryStatus">
                  <option selected>Select service branch</option>
                  {
                    this.loadOptions(FIELD_NAMES.MILITARY)
                  }
                </select>
              </div>
            </Wizard.Page>
            <Wizard.Page>
              <div className="demographics-form-container">
                <label htmlFor="education">Your highest level of education</label>
                <select name="education" id="education">
                  <option selected>Select level of education</option>
                  {
                    this.loadOptions(FIELD_NAMES.EDUCATION_LEVEL)
                  }
                </select>
                <label htmlFor="parentEducation">What is the highest level of education that any of your parents or guardians have achieved?</label>
                <select name="parentEducation" id="parentEducation">
                  <option selected>Select guardian education</option>
                  {
                    this.loadOptions(FIELD_NAMES.PARENT_EDUCATION)
                  }
                </select>
              </div>
            </Wizard.Page>
            <Wizard.Page>
              <div className="demographics-form-container">
                <label htmlFor="workStatus">What is your current work status?</label>
                <select name="workStatus" id="workStatus">
                  <option selected>Select work status</option>
                  {
                    this.loadOptions(FIELD_NAMES.WORK_STATUS)
                  }
                </select>
                <label htmlFor="currentIndustry">What industry do you currently work in?</label>
                <select name="currentIndustry" id="currentIndustry">
                  <option selected>Select current industry</option>
                  {
                    this.loadOptions(FIELD_NAMES.CURRENT_WORK)
                  }
                </select>
                <label htmlFor="prospectiveIndustry">What industry do you want to work in</label>
                <select name="prospectiveIndustry" id="prospectiveIndustry">
                  <option selected>Select prospective industry</option>
                  {
                    this.loadOptions(FIELD_NAMES.FUTURE_WORK)
                  }
                </select>
              </div>
            </Wizard.Page>
            <Wizard.Closer>
              <h3>Thank you! You’re helping make edX better for everyone.</h3>
            </Wizard.Closer>
          </Wizard>
        }
      </div>
    )
  }
}

export { DemographicsCollectionModal };
