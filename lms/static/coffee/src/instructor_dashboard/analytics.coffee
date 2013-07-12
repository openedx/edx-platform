# Analytics Section

# imports from other modules.
# wrap in (-> ... apply) to defer evaluation
# such that the value can be defined later than this assignment (file load order).
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# Analytics Section
class Analytics
  constructor: (@$section) ->
    # gather elements
    @$display                = @$section.find '.distribution-display'
    @$display_text           = @$display.find '.distribution-display-text'
    @$display_graph          = @$display.find '.distribution-display-graph'
    @$display_table          = @$display.find '.distribution-display-table'
    @$distribution_select    = @$section.find 'select#distributions'
    @$request_response_error = @$display.find '.request-response-error'

    @populate_selector => @$distribution_select.change => @on_selector_change()

  reset_display: ->
      @$display_text.empty()
      @$display_graph.empty()
      @$display_table.empty()
      @$request_response_error.empty()

  # fetch and list available distributions
  # `cb` is a callback to be run after
  populate_selector: (cb) ->
    @get_profile_distributions [],
      # on error, print to console and dom.
      error: std_ajax_err => @$request_response_error.text "Error getting available distributions."
      success: (data) =>
        # replace loading text in drop-down with "-- Select Distribution --"
        @$distribution_select.find('option').eq(0).text "-- Select Distribution --"

        # add all fetched available features to drop-down
        for feature in data.available_features
          opt = $ '<option/>',
            text: data.display_names[feature]
            data:
              feature: feature

          @$distribution_select.append opt

        # call callback if one was supplied
        cb?()

  # display data
  on_selector_change: ->
    opt = @$distribution_select.children('option:selected')
    feature = opt.data 'feature'

    @reset_display()
    return unless feature
    @get_profile_distributions [feature],
      error: std_ajax_err => @$request_response_error.text "Error getting distribution for '#{feature}'."
      success: (data) =>
        feature_res = data.feature_results[feature]
        # feature response format: {'error': 'optional error string', 'type': 'SOME_TYPE', 'data': [stuff]}
        if feature_res.error
          console.warn(feature_res.error)
          @$display_text.text 'Error fetching data'
        else
          if feature_res.type is 'EASY_CHOICE'
            # display on SlickGrid
            options =
              enableCellNavigation: true
              enableColumnReorder: false
              forceFitColumns: true

            columns = [
              id: feature
              field: feature
              name: feature
            ,
              id: 'count'
              field: 'count'
              name: 'Count'
            ]

            grid_data = _.map feature_res.data, (value, key) ->
              datapoint = {}
              datapoint[feature] = feature_res.display_names[key]
              datapoint['count'] = value
              datapoint

            table_placeholder = $ '<div/>', class: 'slickgrid'
            @$display_table.append table_placeholder
            grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
          else if feature is 'year_of_birth'
            graph_placeholder = $ '<div/>', class: 'year-of-birth'
            @$display_graph.append graph_placeholder

            graph_data = _.map feature_res.data, (value, key) -> [parseInt(key), value]

            $.plot graph_placeholder, [
              data: graph_data
            ]
          else
            console.warn("don't know how to show #{feature_res.type}")
            @$display_text.text 'Unavailable Metric\n' + JSON.stringify(feature_res)


  # fetch distribution data from server.
  # `handler` can be either a callback for success
  # or a mapping e.g. {success: ->, error: ->, complete: ->}
  get_profile_distributions: (featurelist, handler) ->
    settings =
      dataType: 'json'
      url: @$distribution_select.data 'endpoint'
      data: features: JSON.stringify featurelist

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Analytics: Analytics
