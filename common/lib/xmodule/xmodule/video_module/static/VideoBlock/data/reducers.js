export const updateSettings = (state, {payload}) => {
  return {...state, settings: payload.settings}
};

export const updateChanges = (state, {payload}) => {
  return {...state, changes: payload.changes}
}

export const setErrors = (state, {payload}) => {
  return {...state, errors: payload.errors}
}

export const genReducer = (reducingFunctions) => (state, action) => {
  if (!action) {
    return state
  }
  if (reducingFunctions[action.type]) {
    state = reducingFunctions[action.type](state, action)
  }
  return state
};

export const rootReducer = genReducer({updateSettings, updateChanges, setErrors});
