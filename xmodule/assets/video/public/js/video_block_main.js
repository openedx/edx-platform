import {test} from './video_storage';

console.log('In video_block_main.js file');

window.Video = function (runtime, element) {
  'use strict';
  console.log('In Video initialize method');
  test();
}
