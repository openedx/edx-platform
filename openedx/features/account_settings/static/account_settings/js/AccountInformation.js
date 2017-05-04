import React, { Component } from 'react';
import ReactDOM from 'react-dom';

import { TabInterface, TextInput, SelectInput } from 'excalibur';

class AccountInformation extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
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
      preferredLanguageOptions = this.transformOptions(fieldsData.preferred_language.options, true);

    return (
      <div key="0" className="py-2">
        <p>
          These settings include basic information about your account.
          You can also specify additional information and see your linked
          social accounts on this page.
        </p>
        <h3>Basic Account Information</h3>
        <form>
          <TextInput
            className="py-2 my-2"
            value={accountData.name}
            name="fullname"
            label="Full Name"
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
            description="The email address you use to sign in. Communications from
            {platformName} and your courses are sent to this address."
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.email}
            options={languageOptions}
            name="language"
            label="Language"
            description="The language used throughout this site. This site is currently
            available in a limited number of languages."
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.email}
            options={locationOptions}
            name="country"
            label="Country or Region"
          />
          <SelectInput
            className="py-2 my-2"
            value={preferencesData.time_zone}
            options={timezoneOptions}
            name="time_zone"
            label="Time Zone"
            description="Select the time zone for displaying course dates. If you do
            not specify a time zone, course dates, including assignment deadlines, will
            be displayed in your browser's local time zone."
          />
        </form>
        <h3>Additional Information</h3>
        <form>
          <SelectInput
            className="py-2 my-2"
            value={accountData.level_of_education}
            options={educationOptions}
            name="level_of_education"
            label="Education Completed"
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.gender}
            options={genderOptions}
            name="gender"
            label="Gender"
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.year_of_birth}
            options={birthYearOptions}
            name="year_of_birth"
            label="Year of Birth"
          />
          <SelectInput
            className="py-2 my-2"
            value={accountData.preferred_language}
            options={preferredLanguageOptions}
            name="preferred_language"
            label="Preferred Language"
          />
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
