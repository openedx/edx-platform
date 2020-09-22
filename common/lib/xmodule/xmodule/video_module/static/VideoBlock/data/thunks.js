import { getSettings, postSettings } from './api';

export const fetchSettings = ({ runtime, xblockElement }) => async (dispatch) => {
  const settings = await getSettings({ runtime, xblockElement }).catch((error) => {
    throw error
  });
  dispatch({type: 'updateSettings', payload: {settings}})
  dispatch({type: 'updateChanges', payload: {changes: settings}})
}

export const submitSettings = ({ runtime, xblockElement, changes }) => async (dispatch) => {
  const notify = (label, data) => {
    if (runtime.notify) {
      runtime.notify(label, data)
    }
  }
  notify('save', {state: 'start'})
  return postSettings({runtime, xblockElement, changes}).then((settings) => {
    dispatch({type: 'updateSettings', payload: {settings}})
    notify('save', {state: 'end'});
    return settings
  }).catch((error) => {
    let message = gettext('We had an error saving this component. Please check the form and try again.')
    const errorData = error.data || {}
    if (errorData.detail) {
      message = error.detail
    }
    if (errorData.errors) {
      dispatch({type: 'setErrors', payload: {errors: errorData.errors}})
    }
    notify('error', {title: gettext('Error Saving Video'), message: message});
    throw error
  })
}

export const emit = (type, data) => async (dispatch) => {
  dispatch({type, payload: data})
}
