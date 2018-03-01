import React from 'react';

import EntitlementModalContainer from '../EntitlementModal/EntitlementModalContainer'

class Main extends React.Component{
	constructor(props){
		super(props);
	}

	render(){
		return(
			<div>
				<h1>
					Entitlement Support Page
				</h1>
				<Button
	        className={['btn', 'btn-primary']}
	        label= "Create New Entitlement"
	        onClick={this.openCreationModal.bind(this)}
			  />
				<EntitlementModalContainer supportReasons={this.props.supportReasons}/>
			</div>
		)
	}
}

export default Main;