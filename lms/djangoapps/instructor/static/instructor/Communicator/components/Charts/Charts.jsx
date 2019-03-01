import React from 'react';

const d3 = require('../d3.min.js');
import PropTypes from 'prop-types';
import * as crossfilter from 'crossfilter2';

import Spacer from '../Spacer';

/**
 * The Charts component holds all logic
 * necessary to render the Attrition,
 * Certification, and Completion interactive
 * charts, as well as the filtering functions
 * necessary to manipulate the underlying data.
 */
export class Charts extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      /**
       * @param {Object} filterLimits the percentile limits to use
       * for filtering each chart's students
       */
      filterLimits: {
        'completion-chart': [0, 100],
        'attrition-chart': [0, 100],
        'certification-chart': [0, 100],
      },
    };
    // a dummy crossfilter object used so we can initialize fields dependent on
    // a crossfilter object
    const tempCrossfilter = crossfilter([]);
    // selecting different fields of the crossfilter
    this.completion = tempCrossfilter.dimension(d => d.completion_prediction);
    this.attrition = tempCrossfilter.dimension(d => d.attrition_prediction);
    this.certification = tempCrossfilter.dimension(d => d.certification_prediction);
    // group by integer for graph purposes
    this.completions = this.completion.group(Math.floor);
    this.attritions = this.attrition.group(Math.floor);
    this.certifications = this.certification.group(Math.floor);
    // fetch by anon_user_id
    this.anonUserId = tempCrossfilter.dimension(d => d.anon_user_id);
    // initialize empty charts and chart id lookup hashmap
    this.charts = [];
    this.idLookup = {};

    // denotes if the instance crossfilter objects defined above
    // have been initialized with real data or not
    // if they haven't, the first chart render call
    // will initialize all of them with fetched data
    // passed from Communicator
    this.initialized = false;

    // bind class functions to `this`
    this.onAttrClick = this.onAttrClick.bind(this);
    this.onCompNoCertClick = this.onCompNoCertClick.bind(this);
    this.filter = this.filter.bind(this);
  }

  componentDidMount() {
    // pass Charts' filter function to Communicator parent upon mount
    this.props.syncChart({
      filter: this.filter,
    });
  }

  shouldComponentUpdate(nextProps, nextState) {
    // we should only update if filter limits or data change
    // this is because the process of rendering the d3 graphs to DOM will
    // continually trigger rerenders unless we interrupt it
    if (nextProps.filteredStudents !== this.props.filteredStudents) {
      return true;
    }
    // deep equality check
    if (JSON.stringify(nextState.filterLimits) !== JSON.stringify(this.state.filterLimits)) {
      return true;
    }
    return false;
  }

  componentDidUpdate() {
    // rerender the charts in DOM if our props / state have changed
    // needed because d3 renders directly to DOM rather than thru React
    this.renderCharts(this.props.allStudents, this.props.filteredStudents);
  }

  /**
   * Sets the filter limits to a preset for
   * predicted to attrit and not complete the course
   */
  onAttrClick() {
    // TODO(Jeff): document these numbers
    const limits = [[0, 70], [80, 100], [0, 70]];
    this.charts.forEach((c, i) => {
      c.filter(limits[i]);
    });
  }

  /**
   * Sets the filter limits to a preset for
   * predicted to complete but not earn a cert
   */
  onCompNoCertClick() {
    // TODO(Jeff): document these numbers
    const limits = [[80, 100], null, [0, 20]];
    this.charts.forEach((c, i) => {
      c.filter(limits[i]);
    });
  }

  /**
   * Renders a single bar chart.
   * @param {String} htmlId the html `id` of the div to render this chart to
   */
  barChart(htmlId) {
    if (!this.barChart.id) this.barChart.id = 0;
    let id;

    // initialize the chart id in the lookup map
    // if we've already initialized chart in the DOM, just find the id in the lookup map
    if (!(htmlId in this.idLookup)) {
      this.idLookup[htmlId] = this.barChart.id;
      // eslint-disable-next-line prefer-destructuring
      id = this.barChart.id;
    } else {
      id = this.idLookup[htmlId];
    }

    // initialize chart properties
    let margin = {
      top: 10,
      right: 10,
      bottom: 20,
      left: 10,
    };
    let x;
    let y = d3.scale.linear().range([100, 0]);
    this.barChart.id += 1;
    const axis = d3.svg.axis().orient('bottom');
    const brush = d3.svg.brush();
    let brushDirty;
    let dimension;
    let group;
    let round;
    let all;

    /**
     * Render the actual chart itself according to the parameters set above.
     */
    const chart = () => {
      const width = x.range()[1];
      const height = y.range()[0];
      y.domain([0, all.top(1)[0].value]);

      const div = d3.select(`#${htmlId}`);
      let g = div.select('g');

      const resizePath = (d) => {
        const e = +(d === 'e');
        // eslint-disable-next-line no-shadow
        const x = e ? 1 : -1;
        // eslint-disable-next-line no-shadow
        const y = height / 3;
        // eslint-disable-next-line prefer-template
        return 'M' + (0.5 * x) + ',' + y
          + 'A6,6 0 0 ' + e + ' ' + (6.5 * x) + ',' + (y + 6)
          + 'V' + ((2 * y) - 6)
          + 'A6,6 0 0 ' + e + ' ' + (0.5 * x) + ',' + (2 * y)
          + 'Z'
          + 'M' + (2.5 * x) + ',' + (y + 8)
          + 'V' + ((2 * y) - 8)
          + 'M' + (4.5 * x) + ',' + (y + 8)
          + 'V' + ((2 * y) - 8);
      };

      // Create the skeletal chart.
      if (g.empty()) {
        g = div.append('svg')
          .attr('width', width + margin.left + margin.right)
          .attr('height', height + margin.top + margin.bottom)
          .append('g')
          .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')'); // eslint-disable-line prefer-template

        g.append('clipPath')
          .attr('id', 'clip-' + id) // eslint-disable-line prefer-template
          .append('rect')
          .attr('width', width)
          .attr('height', height);
        g.selectAll('.bar')
          .data(['background', 'foreground'])
          .enter().append('path')
          .attr('class', d => d + ' bar') // eslint-disable-line prefer-template
          .datum(group.all());

        g.selectAll('.foreground.bar')
          .attr('clip-path', 'url(#clip-' + id + ')'); // eslint-disable-line prefer-template

        g.append('g')
          .attr('class', 'axis')
          .attr('transform', 'translate(0,' + height + ')') // eslint-disable-line prefer-template
          .call(axis);

        // Initialize the brush component with pretty resize handles.
        const gBrush = g.append('g').attr('class', 'brush').call(brush);
        gBrush.selectAll('rect').attr('height', height);
        gBrush.selectAll('.resize').append('path').attr('d', resizePath);
      }

      // Only redraw the brush if set externally.
      if (brushDirty) {
        brushDirty = false;
        g.selectAll('.brush').call(brush);
        if (brush.empty()) {
          g.selectAll('#clip-' + id + ' rect') // eslint-disable-line prefer-template
            .attr('x', 0)
            .attr('width', width);
        } else {
          const extent = brush.extent();
          g.selectAll('#clip-' + id + ' rect') // eslint-disable-line prefer-template
            .attr('x', x(extent[0]))
            .attr('width', x(extent[1]) - x(extent[0]));
        }
      }

      // generate the path for each bar
      const barPath = (groups) => {
        const path = [];
        let i = -1;
        const n = groups.length;
        let d;
        i += 1;
        while (i < n) {
          d = groups[i];
          path.push('M', x(d.key), ',', height, 'V', y(d.value), 'h9V', height);
          i += 1;
        }
        return path.join('');
      };

      g.selectAll('.bar').attr('d', barPath);
    };

    // remove the reset button when we start selecting a range using the mouse
    brush.on('brushstart.chart', () => {
      const div = d3.select(`#${htmlId}`);
      div.select('.title button').style('display', null);
    });

    // filter as the range selected changes
    brush.on('brush.chart', () => {
      const g = d3.select(`#${htmlId}`).select('g');
      let extent = brush.extent();
      if (round) {
        g.select('.brush')
          .call(brush.extent(extent = extent.map(round)))
          .selectAll('.resize')
          .style('display', null);
      }
      g.select('#clip-' + id + ' rect') // eslint-disable-line prefer-template
        .attr('x', x(extent[0]))
        .attr('width', x(extent[1]) - x(extent[0]));
      dimension.filterRange(extent);
      // Get name of chart and limits for that chart
      this.setState({
        filterLimits: {
          ...this.state.filterLimits,
          [`${htmlId}`]: extent,
        },
      });
      this.props.syncChart({
        filterLimits: this.state.filterLimits,
      });
    });

    // display the reset button only if mouse selected something
    // if mouse didn't select anything, reset filters and remove the reset button
    brush.on('brushend.chart', () => {
      if (brush.empty()) {
        const div = d3.select(`#${htmlId}`);
        div.select('.title button').style('display', 'none');
        div.select('#clip-' + id + ' rect').attr('x', null).attr('width', '100%'); // eslint-disable-line prefer-template
        dimension.filterAll();
      }
    });

    // sets the chart's margins
    chart.margin = (_) => {
      if (!_) return margin;
      margin = _;
      return chart;
    };

    // sets the chart's x dimension
    chart.x = (_) => {
      if (!_) return x;
      x = _;
      axis.scale(x);
      brush.x(x);
      return chart;
    };


    // sets the chart's y dimension
    chart.y = (_) => {
      if (!_) return y;
      y = _;
      return chart;
    };

    // sets the chart's X data
    chart.dimension = (_) => {
      if (!_) return dimension;
      dimension = _;
      return chart;
    };

    // sets the chart's reference unfiltered data
    chart.all = (_) => {
      if (!_) return all;
      all = _;
      return chart;
    };

    /**
     * Filters the chart according to the range given
     * @param {Array<number>} _ an array of two integers 0-100
     * denoting the minimum and maximum filter range/extent respectively
     */
    chart.filter = (_) => {
      if (_) {
        brush.extent(_);
        dimension.filterRange(_);
        this.setState({
          filterLimits: {
            ...this.state.filterLimits,
            [`${htmlId}`]: _,
          },
        });
      } else {
        brush.clear();
        dimension.filterAll();
        this.setState({
          filterLimits: {
            ...this.state.filterLimits,
            [`${htmlId}`]: [0, 100],
          },
        });
      }
      this.props.syncChart(this.state.filterLimits);
      brushDirty = true;
      chart();
      return chart;
    };

    // sets the chart's Y data
    chart.group = (_) => {
      if (!_) return group;
      group = _;
      return chart;
    };

    // sets whether we should round Y data values
    chart.round = (_) => {
      if (!_) return round;
      round = _;
      return chart;
    };
    return d3.rebind(chart, brush, 'on');
  }

  /**
   * Filters all charts according to the given filters.
   * This function is passed to the parent Communicator
   * and is the programmatic way to filter both the chart UX
   * and the underlying crossfilter object.
   * @param {Array<Array<number>>} filters an array of 3 arrays, each
   * containing filter ranges
   */
  filter(filters) {
    for (let i = 0; i < this.charts.length; i += 1) {
      this.charts[i].filter(filters[i]);
    }
  }

  // resets the ith chart's filter, where i is 0-2 inclusive
  reset(i) {
    this.charts[i].filter(null);
  }

  /**
   * Rerenders all charts with the given data.
   * @param {crossfilter} allStudents an unfiltered crossfilter object containing all student data
   * @param {crossfilter} students a crossfilter object that has been filtered by chart filters
   */
  renderCharts(allStudents, students) {
    // if we aren't given data don't do anything
    if (!students || !allStudents) {
      return null;
    }

    // initialize the selectors of crossfilter data with real data
    // in this class if we haven't already
    if (!this.initialized) {
      this.completion = students.dimension(d => d.completion_prediction);
      this.attrition = students.dimension(d => d.attrition_prediction);
      this.certification = students.dimension(d => d.certification_prediction);
      this.completions = this.completion.group(Math.floor);
      this.attritions = this.attrition.group(Math.floor);
      this.certifications = this.certification.group(Math.floor);
      this.anonUserId = students.dimension(d => d.anon_user_id);

      this.initialized = true;
    }

    // generate our charts
    const charts = [
      this.barChart('completion-chart')
        .all(allStudents.dimension(d => d.completion_prediction).group(Math.floor))
        .dimension(this.completion)
        .group(this.completions)
        .x(d3.scale.linear()
          .domain([0, 100])
          .rangeRound([0, 900])),
      this.barChart('attrition-chart')
        .all(allStudents.dimension(d => d.attrition_prediction).group(Math.floor))
        .dimension(this.attrition)
        .group(this.attritions)
        .x(d3.scale.linear()
          .domain([0, 100])
          .rangeRound([0, 900])),
      this.barChart('certification-chart')
        .all(allStudents.dimension(d => d.certification_prediction).group(Math.floor))
        .dimension(this.certification)
        .group(this.certifications)
        .x(d3.scale.linear()
          .domain([0, 100])
          .rangeRound([0, 900])),
    ];

    // render each chart
    charts.forEach(chart => chart());
    // set the charts attribute so we can use it later
    this.charts = charts;
    // force a rerender of the parent Communicator so we have accurate
    // selected student count values in the email form UI
    this.props.forceRerender();
    return charts;
  }

  render() {
    return (
      <div>
        {/* preset filter value option buttons */}
        <p style={{ clear: 'left', marginTop: '30px' }}>
          Analytics pre-sets to try: {/* es-lint-disable no-trailing-spaces */}
          <button type="button" id="comp-no-cert" onClick={this.onCompNoCertClick}>
            Predicted to complete but not to earn a certificate
          </button>
          <div style={{ width: 5, height: 10, display: 'inline-block' }} />
          <button type="button" id="attr-no-comp-cert" onClick={this.onAttrClick}>
            Predicted to attrit and not complete
          </button>
        </p>
        <Spacer />

        {/* the chart containers - all actual chart rendering is done directly in the DOM by d3 */}
        <div id="charts">
          <div id="completion-chart" className="chart">
            <div className="title">
              Completion % chance{' '}
              <button
                className="reset"
                onClick={() => this.reset(0)}
                style={{
                  display: 'none',
                  color: 'black',
                }}
              >
                reset
              </button>
            </div>
          </div>
          <div id="attrition-chart" className="chart">
            <div className="title">
              Attrition % chance{' '}
              <button
                className="reset"
                onClick={() => this.reset(1)}
                style={{
                  display: 'none',
                  color: 'black',
                }}
              >
                reset
              </button>
            </div>
          </div>
          <div id="certification-chart" className="chart">
            <div className="title">
              Certification % chance{' '}
              <button
                className="reset"
                onClick={() => this.reset(2)}
                style={{
                  display: 'none',
                  color: 'black',
                }}
              >
                reset
              </button>
            </div>
          </div>
        </div>

        {/* counts for number and percentage of students selected by the filters */}
        <aside id="totals">
          <span id="active">
            {`${(this.anonUserId.top(Infinity).length > 0 ? this.anonUserId.top(Infinity).length : '-')} `}
          </span>
          <span id="percentage">
            ({Math.round((this.anonUserId.top(Infinity).length * 100) / this.props.allStudents.size())}%){' '}
          </span>
          of{' '}
          <span id="total">{this.props.allStudents.size() > 0 ? this.props.allStudents.size() : '-'}</span>
          {' '}learners selected{' '}
        </aside>
      </div>
    );
  }
}

Charts.propTypes = {
  filteredStudents: PropTypes.objectOf(crossfilter).isRequired,
  allStudents: PropTypes.objectOf(crossfilter).isRequired,
  forceRerender: PropTypes.func.isRequired,
  syncChart: PropTypes.func.isRequired,
};
export default Charts;
