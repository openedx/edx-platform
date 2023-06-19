import Cookies from 'js-cookie';
import 'whatwg-fetch';

const COURSE_BLOCKS_API = '/api/courses/v1/blocks/';
const PROGRAM_MAPPING_API = '/genplus/assessment/api/v1/program-mapping'

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken')
};

export function buildQueryString(data) {
  return Object.keys(data)
    .map((key) => {
      const value = Array.isArray(data[key])
        ? data[key].map(item => encodeURIComponent(item)).join(',')
        : encodeURIComponent(data[key]);
      return `${encodeURIComponent(key)}=${value}`;
    })
    .join('&');
}

export const getCourseBlocks = (baseUrl, courseId) => fetch(
  `${baseUrl}${COURSE_BLOCKS_API}?${buildQueryString({
    course_id: courseId,
    all_blocks: true,
    depth: 'all',
    requested_fields: ['name', 'display_name', 'block_type', 'children'],
  })}`, {
    credentials: 'include',
    method: 'get',
    headers: HEADERS,
  },
);


export const getProgramQuestionsMapping = (programSlug) => fetch(
  `${PROGRAM_MAPPING_API}/${programSlug}`, {
    credentials: 'include',
    method: 'get',
    headers: HEADERS,
  },
)

export const addProgramQuestionsMapping = (programSlug, mappingData) => fetch(
  `${PROGRAM_MAPPING_API}/${programSlug}/`, {
    method: 'post',
    mode: "cors",
    credentials: 'include',
    headers: HEADERS,
    body: JSON.stringify(mappingData)
  },
)
