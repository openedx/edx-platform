import React from 'react';
import {render} from 'react-dom';

//Import components
import MainContainer from './components/Main/MainContainer';

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