import React from 'react';
import { InputText } from '@edx/paragon';
import PropTypes from 'prop-types';


class Search extends React.Component {
  constructor(props) {
    super(props);
    this.state = { username: '' };

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleUsernameChange = this.handleUsernameChange.bind(this);
  }

  handleSubmit(event) {
    event.preventDefault();
    // updating state will cause react to re-render dom, the default refresh is unneeded
    this.props.fetchEntitlements(this.state.username);
  }

  handleUsernameChange(username) {
    this.setState({ username });
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit} className="col-md-3 search-form">
        <InputText
          name="username"
          label="Search by Username"
          value={this.state.username}
          onChange={this.handleUsernameChange}
        />
        <input
          type="submit"
          hidden
        />
      </form>
    );
  }
}

Search.propTypes = {
  fetchEntitlements: PropTypes.func.isRequired,
};

export default Search;
