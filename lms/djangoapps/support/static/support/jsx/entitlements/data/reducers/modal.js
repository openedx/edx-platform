import ACTION_TYPES from '../actions/actionCreators';

function modal(state = {}, action){
	const i = action.index;
	// if action.type = ACTION_TYPES.
	console.log('modeal reducer receiving action type:',action.type)
	switch(action.type){
		case 'OPEN_REISSUE_MODAL':
			console.log('OPEN_REISSUE_MODAL reduce for entitlement',action.entitlement )
			return Object.assign({}, state, {isOpen:true, activeEntitlement:action.entitlement});
		case 'OPEN_CREATION_MODAL':
			console.log('OPEN_CREATION_MODAL reduced')
			return Object.assign({}, state, {isOpen:true, activeEntitlement:null});
		case 'CLOSE_MODAL':
			console.log('CLOSE_MODAL reduce')
			return clearModal();
		case 'UPDATE_ENTITLEMENT_SUCCESS':
			return clearModal();
		case 'CREATE_ENTITLEMENT_SUCCESS':
			return clearModal();
		default: 
			return state;
	}
}

function clearModal(state){
	return Object.assign({}, state, {isOpen:false, activeEntitlement:null});
}

export default modal;