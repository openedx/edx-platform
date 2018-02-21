import React from 'react';
import { Button } from '@edx/paragon';
import SearchContainer from '../EntitlementSearch/SearchContainer';
import EntitlementModalContainer from '../EntitlementModal/EntitlementModalContainer'
import EntitlementTable from '../EntitlementTable/EntitlementTable';

class Main extends React.Component{
	constructor(props){
		super(props);
	}

	openCreationModal(){
		this.props.openCreationModal()
	}

	render(){
		return(
			<div>
				<h1>
					Entitlement Support Page
				</h1>
				<SearchContainer/>
				<Button
			        className={['btn', 'btn-primary']}
			        label= "Create New Entitlement"
			        onClick={this.openCreationModal.bind(this)}
			  />
		    <EntitlementModalContainer supportReasons={this.props.supportReasons}/>
		    <EntitlementTable {...this.props}/>
			</div>
		)
	}
}

export default Main;