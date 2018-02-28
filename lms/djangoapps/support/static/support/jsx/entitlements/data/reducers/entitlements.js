function entitlements(state = [], action){
	switch(action.type){
		case 'FETCH_ENTITLEMENTS_SUCCESS':
			return action.entitlements
		case 'FETCH_ENTITLEMENTS_FAILURE':
			console.log('Fetching entitlements failed', action.error)
			return state
		case 'UPDATE_ENTITLEMENT_SUCCESS':
			//Search through entitlement list in store and replace the updated entitlement with the entitlement from the action
			return state.map(entitlement=>{
				if (entitlement.uuid === action.entitlement.uuid){ 
					return action.entitlement;
				}
				else {
					return entitlement;
				}
			})
		case 'UPDATE_ENTITLEMENT_FAILURE':
			console.log('Updating entitlement failed', action.error)
			return state;
		case 'CREATE_ENTITLEMENT_SUCCESS':
			return [...state, action.entitlement];
		case 'CREATE_ENTITLEMENT_FAILURE':
			console.log('Creating entitlement failed', action.error)
			return state;
		default: 
			return state;
	}
}

export default entitlements;