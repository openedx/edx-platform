// create reducer handling 2 things
// action
// copy of current state
import ACTION_TYPES from '../actions/actionCreators';

function entitlements(state = [], action){
	const i = action.index;
	// if action.type = ACTION_TYPES.
	console.log('entitlements reducer receiving action type:',action.type)
	switch(action.type){
		case 'FETCH_ENTITLEMENTS_REQUEST':
			console.log('fetching entitlements', action.email, action.username, action.course_key)
			return state
		case 'FETCH_ENTITLEMENTS_SUCCESS':
			console.log('Fetching entitlements success', action.entitlements)
			return action.entitlements
		case 'FETCH_ENTITLEMENTS_FAILURE':
			console.log('Fetching entitlements failed', action.error)
			return state
		case 'UPDATE_ENTITLEMENT_REQUEST':
			return state
		case 'UPDATE_ENTITLEMENT_SUCCESS':
			//Search through entitlement list in store and replace the updated entitlement with the entitlement from the action
			return state.map(entitlement=>{ 
				console.log('entitlement uuid:', entitlement.uuid)
				console.log('action entitlement:', action.entitlement)
				console.log('action entitlement uuid:', action.entitlement.uuid)
				if(entitlement.uuid === action.entitlement.uuid){ 
					return action.entitlement;
				}
				else{
					return entitlement;
				}
			})
		case 'UPDATE_ENTITLEMENT_FAILURE':
			console.log('updating entitlement failed', action.error)
			return state;
		case 'CREATE_ENTITLEMENT_REQUEST':
			return state;
		case 'CREATE_ENTITLEMENT_SUCCESS':
			return [...state, action.entitlement] ;
		case 'CREATE_ENTITLEMENT_FAILURE':
			console.log('Creating entitlement failed', action.error)
			return state;
		default: 
			return state;
	}
}

export default entitlements;