import React from 'react';
import ReactDOM from 'react-dom';
import { Dropdown } from 'paragon';

export class DropdownMenu extends React.Component {
  static insertIf (property, entry) {
    return property ? entry : [];
  }

  render() {
    const menuContent = [
      {
        title: gettext('Content'),
        menuItems: [
          { label: gettext('Outline'), href: this.props.index_url },
          { label: gettext('Updates'), href: this.props.course_info_url },
          { label: gettext('Pages'), href: this.props.tabs_url },
          { label: gettext('Files & Uploads'), href: this.props.assets_url },
          { label: gettext('Textbooks'), href: this.props.textbooks_url },
          ...DropdownMenu.insertIf(
            this.props.video_pipeline_configured,
            { label: gettext('Video Uploads'), href: this.props.video_url }
          )
        ],
      },
      {
        title: gettext('Settings'),
        menuItems: [
          { label: gettext('Schedule & Details'), href: this.props.settings_url },
          { label: gettext('Grading'), href: this.props.grading_url },
          { label: gettext('Course Team'), href: this.props.course_team_url },
          { label: gettext('Group Configurations'), href: this.props.group_config_url },
          { label: gettext('Advanced Settings'), href: this.props.advanced_settings_url },
          ...DropdownMenu.insertIf(
            this.props.certificates_url,
            { label: gettext('Certificates'), href: this.props.certificates_url }
          )
        ],
      },
      {
        title: gettext('Tools'),
        menuItems: [
          { label: gettext('Import'), href: this.props.import_url },
          { label: gettext('Export'), href: this.props.export_url },
          ...DropdownMenu.insertIf(
            this.props.export_git_url,
            { label: gettext('Export to Git'), href: this.props.export_git_url }
          )
        ],
      },
    ];

    return (
      <ol>
        {menuContent.map((menu, i) => (
          <li className="nav-item" key={i}>
            <Dropdown {...menu} />
          </li>
        ))}
      </ol>
    );
  }
}

export class DropdownRenderer {
  constructor({selector, context}) {
    ReactDOM.render(
      <DropdownMenu {...context} />,
      document.querySelector(selector)
    );
  }
}
