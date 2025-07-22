import React from 'react';
import { Button, Form, InputGroup } from '@openedx/paragon';
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

    handleUsernameChange(event) {
        this.setState({ username: event.target.value });
    }

    render() {
        return (
            <form onSubmit={this.handleSubmit} className="col-md-3 search-form">
                <Form.Group>
                    <Form.Label>Search by Username</Form.Label>
                    <InputGroup>
                        <Form.Control
                            name="username"
                            className="search-field"
                            value={this.state.username}
                            onChange={this.handleUsernameChange}
                        />
                        <InputGroup.Append>
                            <Button 
                                variant="primary" 
                                className="ml-2 search-button" 
                                type="submit"
                            >
                                Search
                            </Button>
                        </InputGroup.Append>
                    </InputGroup>
                </Form.Group>
            </form>
        );
    }
}

Search.propTypes = {
    fetchEntitlements: PropTypes.func.isRequired,
};

export default Search;
