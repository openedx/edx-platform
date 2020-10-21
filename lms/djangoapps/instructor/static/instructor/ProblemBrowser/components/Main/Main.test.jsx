/* global jest,test,describe,expect */
import { Button } from '@edx/paragon';
import { BlockBrowser } from 'BlockBrowser';
import { shallow } from 'enzyme';
import React from 'react';
import renderer from 'react-test-renderer';

import Main from './Main';

describe('ProblemBrowser Main component', () => {
  const courseId = 'testcourse';
  const excludedBlockTypes = [];

  test('render with basic parameters', () => {
    const component = renderer.create(
      <Main
        courseId={courseId}
        excludeBlockTypes={excludedBlockTypes}
        fetchCourseBlocks={jest.fn()}
        onSelectBlock={jest.fn()}
        selectedBlock={null}
      />,
    );
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });

  test('render with selected block', () => {
    const component = renderer.create(
      <Main
        courseId={courseId}
        excludeBlockTypes={excludedBlockTypes}
        fetchCourseBlocks={jest.fn()}
        onSelectBlock={jest.fn()}
        selectedBlock={'some-selected-block'}
      />,
    );
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });

  test('fetch course block on toggling dropdown', () => {
    const fetchCourseBlocksMock = jest.fn();
    const component = renderer.create(
      <Main
        courseId={courseId}
        excludeBlockTypes={excludedBlockTypes}
        fetchCourseBlocks={fetchCourseBlocksMock}
        onSelectBlock={jest.fn()}
        selectedBlock={'some-selected-block'}
      />,
    );
    const instance = component.getInstance();
    instance.handleToggleDropdown();
    expect(fetchCourseBlocksMock.mock.calls.length).toBe(1);
  });

  test('display dropdown on toggling dropdown', () => {
    const component = shallow(
      <Main
        courseId={courseId}
        excludeBlockTypes={excludedBlockTypes}
        fetchCourseBlocks={jest.fn()}
        onSelectBlock={jest.fn()}
        selectedBlock={'some-selected-block'}
      />,
    );
    component.find(Button).simulate('click');
    expect(component.find(BlockBrowser)).toBeTruthy();
  });
});
