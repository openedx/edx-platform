import 'whatwg-fetch';
import Cookies from 'js-cookie';

const COURSE_BLOCKS_API = '/api/courses/v1/blocks/';

const HEADERS = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    'X-CSRFToken': Cookies.get('csrftoken'),
};

const getCourseBlocks = (courseId) => fetch(
    `${COURSE_BLOCKS_API}/?course_id=${encodeURIComponent(courseId)}&all_blocks=true&depth=all&requested_fields=name,display_name,block_type,children`, {
        credentials: 'same-origin',
        method: 'get',
        headers: HEADERS,
    },
);

export {
    getCourseBlocks,
};
