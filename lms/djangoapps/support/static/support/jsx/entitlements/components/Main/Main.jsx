import React from 'react';

import SearchContainer from '../EntitlementSearch/SearchContainer';

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
				<SearchContainer/>
			{/*Instert main content here*/}
			</div>
		)
	}
}

export default Main;