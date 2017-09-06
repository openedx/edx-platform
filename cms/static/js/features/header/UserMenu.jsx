import React from 'react';
import ReactDOM from 'react-dom';
import { Dropdown } from 'paragon';

export class UserMenuRenderer {
  constructor({selector, context}) {
    let menuItems = [
      { label: gettext(context.studio_name), href: '/' },
      { label: gettext('Sign Out'), href: context.logout_url },
    ];

    if (context.is_global_staff) {
      menuItems.splice(1, 0,
        { label: gettext('Maintenance'), href: context.maintenance_url }
      );
    }

    ReactDOM.render(
      <Dropdown {...context}
        title={context.username}
        menuItems={menuItems}
      />,
      document.querySelector(selector)
    );
  }
}
