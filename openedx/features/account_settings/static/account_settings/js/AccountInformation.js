import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { TabInterface, TextInput, SelectInput } from 'excalibur';

import { patch } from './xhr';

class AccountInformation extends React.Component {
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.state = {
      formData: {},
      changeSuccess: false
    };
  }

  transformOptions(options, leadWithBlank) {
    let opts = options.map(option => {
      return {
        value: option[0],
        label: option[1]
      };
    })
    if (leadWithBlank) {
      opts = [{}, ...opts];
    }
    return opts;
  }

  getTimezoneOptions() {
    return [
      {
        label: 'Default (Local Time Zone)'
      },
      {
        label: 'All Time Zones',
        options: this.transformOptions(this.props.fieldsData.time_zone.options)
      }
    ];
  }

  handleChange(data, name) {
    this.setState({
      formData: {
        [name]: data,
        ...this.state.formData
      }
    });
  }

  handleSubmit(e) {
    e.preventDefault();
    patch(this.props.accountsUrl, this.state.formData)
      .then(response => {
        console.log(response);
      });
  }

  render() {
    const {
        fieldsData,
        platformName,
        accountData,
        preferencesData
      } = this.props,
      tabLabels = [
        'Account Information',
        'Linked Accounts',
        'Order History'
      ],
      languageOptions = this.transformOptions(fieldsData.language.options, true),
      locationOptions = this.transformOptions(fieldsData.country.options, true),
      timezoneOptions = this.getTimezoneOptions(),
      educationOptions = this.transformOptions(fieldsData.level_of_education.options, true),
      genderOptions = this.transformOptions(fieldsData.gender.options, true),
      birthYearOptions = this.transformOptions(fieldsData.year_of_birth.options, true),
      preferredLanguageOptions = this.transformOptions(fieldsData.preferred_language.options, true),
      successMessage = (this.state.changeSuccess) ? (
        <span className="">Changes saved!</span>
      ) : '';

    return (
      <div key="0" className="py-2">
        <p>
          These settings include basic information about your account.
          You can also specify additional information and see your linked
          social accounts on this page.
        </p>
        <form onSubmit={this.handleSubmit} className="py-4">
          <h3>Basic Account Information</h3>
          <TextInput
            className="py-2 my-2"
            value={accountData.name}
            name="fullname"
            label="Full Name"
            onChange={this.handleChange}
            description="The name that is used for ID verification and appears on
            your certificates. Other learners never see your full name. Make sure to
            enter your name exactly as it appears on your government-issued photo ID,
            including any non-Roman characters."
          />
          <TextInput
            className="py-2 my-2"
            value={accountData.email}
            name="email"
            label="Email Address"
            onChange={this.handleChange}
            description={`The email address you use to sign in. Communications from
            ${platformName} and your courses are sent to this address.`}
          />
          <SelectInput
            className="py-2 my-2"
            value={preferencesData['pref-lang']}
            options={languageOptions}
            name="language"
            label="Language"
            onChange={this.handleChange}
            description="The language used throughout this site. This site is currently
            available in a limited number of languages."
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.country}
            options={locationOptions}
            name="country"
            label="Country or Region"
            onChange={this.handleChange}
          />
          <SelectInput
            className="py-2 my-2"
            value={preferencesData.time_zone}
            options={timezoneOptions}
            name="time_zone"
            label="Time Zone"
            onChange={this.handleChange}
            description="Select the time zone for displaying course dates. If you do
            not specify a time zone, course dates, including assignment deadlines, will
            be displayed in your browser's local time zone."
          />
          <input
            type="submit"
            value="Submit"
          />
          {successMessage}
        </form>
        <form onSubmit={this.handleSubmit} className="py-4">
          <h3>Additional Information</h3>
          <SelectInput
            className="py-2 my-2"
            value={accountData.level_of_education}
            options={educationOptions}
            name="level_of_education"
            label="Education Completed"
            onChange={this.handleChange}
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.gender}
            options={genderOptions}
            name="gender"
            label="Gender"
            onChange={this.handleChange}
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.year_of_birth}
            options={birthYearOptions}
            name="year_of_birth"
            label="Year of Birth"
            onChange={this.handleChange}
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.preferred_language}
            options={preferredLanguageOptions}
            name="preferred_language"
            label="Preferred Language"
            onChange={this.handleChange}
          />
          <input
            type="submit"
            value="Submit"
          />
          {successMessage}
        </form>
      </div>
    );
  }
}

AccountInformation.defaultProps = {
  accountData: {},
  preferencesData: {}
};

export default AccountInformation;
