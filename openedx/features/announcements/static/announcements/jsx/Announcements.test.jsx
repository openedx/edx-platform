import React from 'react';
import renderer from 'react-test-renderer';
import testAnnouncements from "./test-announcements.json"

import { AnnouncementSkipLink, AnnouncementList } from "./Announcements"

describe('Announcements component', () => {
  test('render skip link', () => {
    const component = renderer.create(
      <AnnouncementSkipLink />,
    );
    component.root.instance.setState({"count": 10})
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });

  test('render test announcements', () => {
    const component = renderer.create(
      <AnnouncementList />,
    );
    component.root.instance.setState(testAnnouncements);
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });

});
