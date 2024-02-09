import { combineReducers } from 'redux'; // eslint-disable-line
import { blocks, selectedBlock, rootBlock } from 'BlockBrowser/data/reducers'; // eslint-disable-line
import { GET_PROGRAM_SKILL_ASSESSMENT_MAPPING, UPDATE_MAPPING_DATA } from '../actions/actionTypes';

const initialState = {
  mappingData: []
};

export const skillAssessment = (state = initialState, action) => {
  switch (action.type) {
    case GET_PROGRAM_SKILL_ASSESSMENT_MAPPING:
      return {
        ...state,
        mappingData: action.payload.questions_mapping
      }
    case UPDATE_MAPPING_DATA:
      return {
        ...state,
        mappingData: action.payload
      }
    default:
      return state;
  }
};

export default combineReducers({
  blocks,
  selectedBlock,
  rootBlock,
  skillAssessment,
});
