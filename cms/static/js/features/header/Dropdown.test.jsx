import React from 'react';
import { shallow, mount } from 'enzyme';
import { DropdownMenu } from './DropdownRenderer';

const menu_context = {
  'course_key': 'Demo_Course',
  'index_url': 'http://example1.com',
  'course_team_url': 'http://example1.com',
}

describe('<DropdownMenu />', () => {
  it('renders', () => {
    const wrapper = shallow(
      <DropdownMenu
          {...menu_context}
      />,
    );

    const className = wrapper.find('[className="nav-item"]');
    expect(className.exists()).toEqual(true);
  });
});
