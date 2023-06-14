import { combineReducers } from 'redux'; // eslint-disable-line
import { blocks, selectedBlock, rootBlock } from 'BlockBrowser/data/reducers'; // eslint-disable-line
import { GET_PROGRAM_SKILL_ASSESSMENT_MAPPING } from '../actions/actionTypes';

const initialState = {
  mapping: []
};

export const skillAssessmentReducer = (state = initialState, action) => {
  switch (action.type) {
    case GET_PROGRAM_SKILL_ASSESSMENT_MAPPING:
      return {
        ...state,
        mapping: action.payload
      }
    default:
      return state;
  }
};

export default combineReducers({
  blocks,
  selectedBlock,
  rootBlock,
  skillAssessmentReducer,
});
