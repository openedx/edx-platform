/* globals setFixtures */

import Backbone from 'backbone';

import SpecHelpers from 'edx-ui-toolkit/js/utils/spec-helpers/spec-helpers';

import ProgressCircleView from '../views/progress_circle_view';

describe('Progress Circle View', () => {
  let view = null;
  const context = {
    title: 'XSeries Progress',
    label: 'Earned Certificates',
    progress: {
      completed: 2,
      in_progress: 1,
      not_started: 3,
    },
  };

  const testCircle = (progress) => {
    const $circle = view.$('.progress-circle');

    expect($circle.find('.complete').length).toEqual(progress.completed);
    expect($circle.find('.incomplete').length).toEqual(progress.in_progress + progress.not_started);
  };

  const testText = (progress) => {
    const $numbers = view.$('.numbers');
    const total = progress.completed + progress.in_progress + progress.not_started;

    expect(view.$('.progress-heading').html()).toEqual('XSeries Progress');
    expect(parseInt($numbers.find('.complete').html(), 10)).toEqual(progress.completed);
    expect(parseInt($numbers.find('.total').html(), 10)).toEqual(total);
  };

  const getProgress = (x, y, z) => ({
    completed: x,
    in_progress: y,
    not_started: z,
  });

  const initView = (progress) => {
    const data = $.extend({}, context, {
      progress,
    });

    return new ProgressCircleView({
      el: '.js-program-progress',
      model: new Backbone.Model(data),
    });
  };

  const testProgress = (x, y, z) => {
    const progress = getProgress(x, y, z);

    view = initView(progress);
    view.render();

    testCircle(progress);
    testText(progress);
  };

  beforeEach(() => {
    setFixtures('<div class="js-program-progress"></div>');
  });

  afterEach(() => {
    view.remove();
  });

  it('should exist', () => {
    const progress = getProgress(2, 1, 3);

    view = initView(progress);
    view.render();
    expect(view).toBeDefined();
  });

  it('should render the progress circle based on the passed in model', () => {
    const progress = getProgress(2, 1, 3);

    view = initView(progress);
    view.render();
    testCircle(progress);
  });

  it('should render the progress text based on the passed in model', () => {
    const progress = getProgress(2, 1, 3);

    view = initView(progress);
    view.render();
    testText(progress);
  });

  SpecHelpers.withData({
    'should render the progress text with only completed courses': [5, 0, 0],
    'should render the progress text with only in progress courses': [0, 4, 0],
    'should render the progress circle with only not started courses': [0, 0, 5],
    'should render the progress text with no completed courses': [0, 2, 3],
    'should render the progress text with no in progress courses': [2, 0, 7],
    'should render the progress text with no not started courses': [2, 4, 0],
  }, testProgress);
});
