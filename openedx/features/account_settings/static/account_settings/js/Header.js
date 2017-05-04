import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {
  Nav,
  NavItem,
  NavLink,
  NavDropdown,
  DropdownMenu,
  DropdownItem,
  DropdownToggle
} from 'reactstrap';

class Header extends Component {
  constructor(props) {
    super(props);

    this.toggle = this.toggle.bind(this);
    this.state = {
      dropdownOpen: false
    };
  }

  toggle() {
    this.setState({
      dropdownOpen: !this.state.dropdownOpen
    });
  }

  render() {
    return (
      <Nav className="navbar navbar-toggleable-md navbar-dark bg-white">
        <NavItem>
          <button className="navbar-toggler-right btn btn-secondary hidden-lg-up" type="button" data-toggle="collapse" data-target="#mNav" aria-controls="mNav" aria-expanded="false" aria-label="Toggle navigation">
            <span><i className="fa fa-bars mr-2" aria-hidden="true"></i>Menu</span>
          </button>
        </NavItem>
        <NavItem>
          <h1 className="navbar-brand mb-0">
            <NavLink href="#">
              <img src="static/logo.png" alt="edX Home" className="d-inline-block align-top" width="60" height="30" />
            </NavLink>
          </h1>
        </NavItem>
        <NavItem className="navbar-text mr-auto">
          <h2 className="mb-auto h6">
            <b>{this.props.course.number}:</b> {this.props.course.name}
          </h2>
        </NavItem>
        <NavItem>
          <NavLink href="#">Help</NavLink>
        </NavItem>
        <NavDropdown isOpen={this.state.dropdownOpen} toggle={this.toggle}>
          <DropdownToggle nav caret>
            <img src={this.props.user.image} className="rounded mr-1" width="40px" height="40px" />
            {this.props.user.displayName}
          </DropdownToggle>
          <DropdownMenu>
            <DropdownItem>Dashboard</DropdownItem>
            <DropdownItem>Profile</DropdownItem>
            <DropdownItem>Account</DropdownItem>
            <DropdownItem divider />
            <DropdownItem>Sign Out</DropdownItem>
          </DropdownMenu>
        </NavDropdown>
      </Nav>
    );
  }
}

Header.propTypes = {
  course: PropTypes.shape({
    number: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired
  }),
  user: PropTypes.shape({
    displayName: PropTypes.string.isRequired,
    image: PropTypes.string.isRequired
  })
};

export default Header;
