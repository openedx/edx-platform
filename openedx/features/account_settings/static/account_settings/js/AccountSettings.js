import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { TabInterface, TextInput, SelectInput } from 'excalibur';

import AccountInformation from './AccountInformation';
import { get } from './xhr';

class AccountSettingsPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  fetchFormData(url, stateKey) {
    get(url).then(json => {
      this.setState({
        [stateKey]: json
      });
    });
  }

  componentDidMount() {
    this.fetchFormData(this.props.accountsUrl, 'accountData');
    this.fetchFormData(this.props.preferencesUrl, 'preferencesData');
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
        ordersHistoryData,
        platformName
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

    if (!this.state.accountData || !this.state.preferencesData) {
      return <div>loading...</div>;
    }

    return (
      <div>
        <h2>Account Settings</h2>
        <TabInterface
          className="py-3"
          tabLabels={tabLabels}
          panels={[
            <AccountInformation
              {...this.props}
              {...this.state}
            />,
            <div key="1">SECOND PANEL</div>,
            <div key="2">THIRD PANEL</div>,
          ]}
        />
      </div>
    );
  }
}

export class AccountSettings {
  constructor({selector, context}) {
    ReactDOM.render(
      <AccountSettingsPage {...context} />,
      document.querySelector(selector)
    );
  }
}
