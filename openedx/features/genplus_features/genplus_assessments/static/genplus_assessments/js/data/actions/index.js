import { fetchCourseBlocksSuccess } from 'BlockBrowser/data/actions/courseBlocks';
import { getCourseBlocks, getProgramQuestionsMapping, addProgramQuestionsMapping } from '../api/client';
import {
  GET_PROGRAM_SKILL_ASSESSMENT_MAPPING,
  ADD_PROGRAM_SKILL_ASSESSMENT_MAPPING,
  UPDATE_MAPPING_DATA
} from './actionTypes'

const fetchCourseBlocks = (baseUrl, courseId, excludeBlockTypes) => dispatch =>
  getCourseBlocks(baseUrl, courseId)
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      throw new Error(response);
    })
    .then(
      json => dispatch(fetchCourseBlocksSuccess(json, excludeBlockTypes)),
      error => console.log(error), // eslint-disable-line no-console
    );


const fetchProgramSkillAssessmentMapping = (programSlug) => dispatch => {
  getProgramQuestionsMapping(programSlug)
  .then((response) => {
    if (response.ok) {
      return response.json();
    }
    throw new Error(response);
  })
  .then(
      json => dispatch({
        type: GET_PROGRAM_SKILL_ASSESSMENT_MAPPING,
        payload: json
      }),
      error => console.log(error)
  )
}

const addProgramSkillAssessmentMapping = (programSlug, mappingData) => dispatch => {
  addProgramQuestionsMapping(programSlug, mappingData)
  .then((response)=>{
    if (response.ok) {
      return response.json();
    }
    throw new Error(response);
  })
  .then(
    json => dispatch({
      type: ADD_PROGRAM_SKILL_ASSESSMENT_MAPPING,
      payload: json
    }),
    error => console.log(error)
)
}

const updateMappingData = (mappingData) => dispatch => {
  dispatch({
    type: UPDATE_MAPPING_DATA,
    payload: mappingData
  });
}

export {
  fetchCourseBlocks,
  fetchProgramSkillAssessmentMapping,
  addProgramSkillAssessmentMapping,
  updateMappingData
};
