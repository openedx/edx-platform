import { fetchCourseBlocksSuccess } from 'BlockBrowser/data/actions/courseBlocks';
import { getCourseBlocks } from '../api/client';

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

export {
  fetchCourseBlocks
};
