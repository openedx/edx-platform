import React from 'react';
import Main from './Main.jsx';
import renderer from 'react-test-renderer';

test('My first demo test', () => {
  const component = renderer.create(<Main></Main>);
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});
