import React from 'react';
import ReactDOM from 'react-dom';
import { clampHtmlByWords } from './clamp-html';

let container;

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
});

afterEach(() => {
  document.body.removeChild(container);
  container = null;
});

describe('ClampHtml', () => {
  test.each([
    ['', 0, ''],
    ['a b', 0, '…'],
    ['a b', 1, 'a…'],
    ['a  b  c', 2, 'a b…'],
    ['a <i>aa ab</i> b', 2, 'a <i>aa…</i>'],
    ['a <i>aa ab</i> <em>ac</em>', 2, 'a <i>aa…</i>'],
    ['a <i>aa <em>aaa</em></i>', 2, 'a <i>aa…</i>'],
    ['a <i>aa <em>aaa</em> ab</i>', 3, 'a <i>aa <em>aaa…</em></i>'],
    ['a <i>aa ab</i> b c', 4, 'a <i>aa ab</i> b…'],
  ])('clamps by words: %s, %i', (input, wordsLeft, expected) => {
    const div = ReactDOM.render(<div dangerouslySetInnerHTML={{ __html: input }} />, container);
    clampHtmlByWords(div, wordsLeft);
    expect(div.innerHTML).toEqual(expected);
  });
});
