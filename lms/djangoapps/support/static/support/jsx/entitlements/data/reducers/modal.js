function modal(state = {}, action){
	switch(action.type){
		case 'OPEN_REISSUE_MODAL':
			return Object.assign({}, state, {isOpen:true, activeEntitlement:action.entitlement});
		case 'OPEN_CREATION_MODAL':
			return Object.assign({}, state, {isOpen:true, activeEntitlement:null});
		case 'CLOSE_MODAL':
			return clearModal(state);
		case 'UPDATE_ENTITLEMENT_SUCCESS':
			return clearModal(state);
		case 'CREATE_ENTITLEMENT_SUCCESS':
			return clearModal(state);
		default: 
			return state;
	}
}

function clearModal(state){
	return Object.assign({}, state, {isOpen:false, activeEntitlement:null});
}

export default modal;