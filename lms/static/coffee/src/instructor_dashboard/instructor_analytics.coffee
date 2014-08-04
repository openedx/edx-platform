###
Analytics Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments


class ProfileDistributionWidget
  constructor: ({@$container, @feature, @title, @endpoint}) ->
    # render template
    template_params =
      title: @title
      feature: @feature
      endpoint: @endpoint
    template_html = $("#profile-distribution-widget-template").text()
    @$container.html Mustache.render template_html, template_params

  reset_display: ->
      @$container.find('.display-errors').empty()
      @$container.find('.display-text').empty()
      @$container.find('.display-graph').empty()
      @$container.find('.display-table').empty()

  show_error: (msg) ->
    @$container.find('.display-errors').text msg

  # display data
  load: ->
    @reset_display()

    @get_profile_distributions @feature,
      error: std_ajax_err =>
          `// Translators: "Distribution" refers to a grade distribution. This error message appears when there is an error getting the data on grade distribution.`
          @show_error gettext("Error fetching distribution.")
      success: (data) =>
        feature_res = data.feature_results
        if feature_res.type is 'EASY_CHOICE'
          # display on SlickGrid
          options =
            enableCellNavigation: true
            enableColumnReorder: false
            forceFitColumns: true

          columns = [
            id: @feature
            field: @feature
            name: data.feature_display_names[@feature]
          ,
            id: 'count'
            field: 'count'
            name: 'Count'
          ]

          grid_data = _.map feature_res.data, (value, key) =>
            datapoint = {}
            datapoint[@feature] = feature_res.choices_display_names[key]
            datapoint['count'] = value
            datapoint

          table_placeholder = $ '<div/>', class: 'slickgrid'
          @$container.find('.display-table').append table_placeholder
          grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
        else if feature_res.feature is 'year_of_birth'
          graph_placeholder = $ '<div/>', class: 'graph-placeholder'
          @$container.find('.display-graph').append graph_placeholder

          graph_data = _.map feature_res.data, (value, key) -> [parseInt(key), value]

          $.plot graph_placeholder, [
            data: graph_data
          ]
        else
          console.warn("unable to show distribution #{feature_res.type}")
          @show_error gettext('Unavailable metric display.')

  # fetch distribution data from server.
  # `handler` can be either a callback for success
  # or a mapping e.g. {success: ->, error: ->, complete: ->}
  get_profile_distributions: (feature, handler) ->
    settings =
      dataType: 'json'
      url: @endpoint
      data: feature: feature

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings


class GradeDistributionDisplay
  constructor: ({@$container, @endpoint}) ->
    template_params = {}
    template_html = $('#grade-distributions-widget-template').text()
    @$container.html Mustache.render template_html, template_params
    @$problem_selector = @$container.find '.problem-selector'

  reset_display: ->
    @$container.find('.display-errors').empty()
    @$container.find('.display-text').empty()
    @$container.find('.display-graph').empty()

  show_error: (msg) ->
    @$container.find('.display-errors').text msg

  load: ->
    @get_grade_distributions
      error: std_ajax_err => @show_error gettext("Error fetching grade distributions.")
      success: (data) =>
        time_updated = gettext("Last Updated: <%= timestamp %>")
        full_time_updated = _.template(time_updated, {timestamp: data.time})
        @$container.find('.last-updated').text full_time_updated

        # populate selector
        @$problem_selector.empty()
        for {module_id, grade_info} in data.data
          I4X_PROBLEM = /i4x:\/\/.*\/.*\/problem\/(.*)/
          label = (I4X_PROBLEM.exec module_id)?[1]
          label ?= module_id

          @$problem_selector.append $ '<option/>',
            text: label
            data:
              module_id: module_id
              grade_info: grade_info

        @$problem_selector.change =>
          $opt = @$problem_selector.children('option:selected')
          return unless $opt.length > 0
          @reset_display()
          @render_distribution
            module_id:  $opt.data 'module_id'
            grade_info: $opt.data 'grade_info'

        # one-time first selection of first list item.
        @$problem_selector.change()

  render_distribution: ({module_id, grade_info}) ->
    $display_graph = @$container.find('.display-graph')

    graph_data = grade_info.map ({grade, max_grade, num_students}) -> [grade, num_students]
    total_students = _.reduce ([0].concat grade_info),
      (accum, {grade, max_grade, num_students}) -> accum + num_students

    msg = gettext("<%= num_students %> students scored.")
    full_msg = _.template(msg, {num_students: total_students})
    # show total students
    @$container.find('.display-text').text full_msg

    # render to graph
    graph_placeholder = $ '<div/>', class: 'graph-placeholder'
    $display_graph.append graph_placeholder

    graph_data = graph_data

    $.plot graph_placeholder, [
      data: graph_data
      bars: show: true
      color: '#1d9dd9'
    ]


  # `handler` can be either a callback for success
  # or a mapping e.g. {success: ->, error: ->, complete: ->}
  #
  # the data passed to the success handler takes this form:
  # {
  #   "aname": "ProblemGradeDistribution",
  #   "time": "2013-07-31T20:25:56+00:00",
  #   "course_id": "MITx/6.002x/2013_Spring",
  #   "options": {
  #     "course_id": "MITx/6.002x/2013_Spring",
  #   "_id": "6fudge2b49somedbid1e1",
  #   "data": [
  #     {
  #       "module_id": "i4x://MITx/6.002x/problem/Capacitors_and_Energy_Storage",
  #       "grade_info": [
  #         {
  #           "grade": 0.0,
  #           "max_grade": 100.0,
  #           "num_students": 3
  #         }, ... for each grade number between 0 and max_grade
  #   ],
  # }
  get_grade_distributions: (handler) ->
    settings =
      dataType: 'json'
      url: @endpoint
      data: aname: 'ProblemGradeDistribution'

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings


# Analytics Section
class InstructorAnalytics
  constructor: (@$section) ->
    @$section.data 'wrapper', @

    @$pd_containers = @$section.find '.profile-distribution-widget-container'
    @$gd_containers = @$section.find '.grade-distributions-widget-container'

    @pdws = _.map (@$pd_containers), (container) =>
      new ProfileDistributionWidget
        $container: $(container)
        feature:    $(container).data 'feature'
        title:      $(container).data 'title'
        endpoint:   $(container).data 'endpoint'

    @gdws = _.map (@$gd_containers), (container) =>
      new GradeDistributionDisplay
        $container: $(container)
        endpoint:   $(container).data 'endpoint'

  refresh: ->
    for pdw in @pdws
      pdw.load()

    for gdw in @gdws
      gdw.load()

  onClickTitle: ->
    @refresh()


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  InstructorAnalytics: InstructorAnalytics
