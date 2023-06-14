import { fetchCourseBlocksSuccess } from 'BlockBrowser/data/actions/courseBlocks';
import { getCourseBlocks, getProgramQuestionsMapping, addProgramQuestionsMapping } from '../api/client';
import {
  GET_PROGRAM_SKILL_ASSESSMENT_MAPPING,
  ADD_PROGRAM_SKILL_ASSESSMENT_MAPPING
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


const fetchProgramSkillAssessmentMapping = (program_slug) =>{
  getProgramQuestionsMapping(program_slug)
  .then((response)=>{
    if(response.ok){
      return {
        type: GET_PROGRAM_SKILL_ASSESSMENT_MAPPING,
        payload: response.json()
      };
    }
    throw new Error(response);
  })
}

const addProgramSkillAssessmentMapping = (program_slug, mapping_data) =>{
  addProgramQuestionsMapping(program_slug, mapping_data)
  .then((response)=>{
    if(response.ok){
      return {
        type: ADD_PROGRAM_SKILL_ASSESSMENT_MAPPING,
        payload: response.json()
      };
    }
    throw new Error(response);
  })
}

export {
  fetchCourseBlocks,
  fetchProgramSkillAssessmentMapping,
  addProgramSkillAssessmentMapping
};
