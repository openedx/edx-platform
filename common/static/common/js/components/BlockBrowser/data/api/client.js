import Cookies from 'js-cookie';
import 'whatwg-fetch';

const COURSE_BLOCKS_API = '/api/courses/v1/blocks/';

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
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

export const getCourseBlocks = courseId => fetch(
  `${COURSE_BLOCKS_API}?${buildQueryString({
    course_id: courseId,
    all_blocks: true,
    depth: 'all',
    requested_fields: ['name', 'display_name', 'block_type', 'children'],
  })}`, {
    credentials: 'same-origin',
    method: 'get',
    headers: HEADERS,
  },
);
