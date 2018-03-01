import React from 'react';

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
				<EntitlementTable {...this.props}/>
			</div>
		)
	}
}

export default Main;