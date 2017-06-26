import React from 'react';
import ReactDOM from 'react-dom';
import Dropdown from 'paragon/dist/Dropdown.js';

class UserMenu extends React.Component {
  static insertIf (property, entry) {
    return property ? entry : [];
  }

  render() {
    return (
      <Dropdown
        title={this.props.username}
        menuItems={[
          { label: gettext(this.props.studio_name), href: '/' },
          ...UserMenu.insertIf(
            this.props.is_global_staff,
            { label: gettext('Maintenance'), href: this.props.maintenance_url }
          ),
          { label: gettext('Sign Out'), href: this.props.logout_url },
        ]}
      />
    );
  }
}

export class UserMenuRenderer {
  constructor({selector, context}) {
    ReactDOM.render(
      <UserMenu {...context} />,
      document.querySelector(selector)
    );
  }
}
