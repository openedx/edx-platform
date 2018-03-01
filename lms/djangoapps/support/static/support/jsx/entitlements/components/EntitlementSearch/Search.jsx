import React from 'react';
import { InputText } from '@edx/paragon';


class Search extends React.Component{
	constructor(props){
		super(props)
		this.state = {username_or_email: ''}
	}

	handleSubmit(event){
		event.preventDefault(); //prevents the page from refreshing, refresh unneeded since state update will trigger react to update dom
		this.props.fetchEntitlements(this.state.username_or_email);
	}

	handleUserChange(event){
		this.setState({username_or_email: event});
	}

	render(){
		return(
			<form ref="searchForm" className="search-form" onSubmit={this.handleSubmit.bind(this)}>
				<InputText 
					name="username_or_email"
		      label="Search by Usename or Email" 
		      value={this.state.username_or_email} 
		      onChange={this.handleUserChange.bind(this)}/>
				<input type="submit" hidden/>
			</form>
		)
	}
}


export default Search;