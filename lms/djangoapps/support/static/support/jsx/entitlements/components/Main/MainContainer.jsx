import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import * as actionCreators from '../../data/actions/actionCreators';
import Main from './Main';

function mapStateToProps(state){
	console.log('mapping state to props', state)
	return{
		entitlements: state.entitlements,
		modal: state.modal
	}
}

function mapDispatchToProps(dispatch){
	console.log('mapping dispatch to props')
	return bindActionCreators(actionCreators, dispatch);
}

const MainContainer = connect(mapStateToProps,
	mapDispatchToProps)(Main);//takes all the props and data from state and dispatch and maps them to main.



export default MainContainer;