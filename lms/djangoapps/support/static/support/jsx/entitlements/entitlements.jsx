import React from 'react';
import {render} from 'react-dom';

//Import components
import MainContainer from './components/Main/MainContainer';
import SearchContainer from './components/EntitlementSearch/SearchContainer';
import EntitlementTable from './components/EntitlementTable/EntitlementTable';

//Import redux dependecies
import {Provider } from 'react-redux';
import store, {history} from './store';

export class EntitlementSupportPage extends React.Component {
	constructor(props){
		super(props)
	}
	render(){
		return	(
			<Provider store={store} >
				<MainContainer {...this.props}/>
			</Provider>
		)
	}
}