log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


class Analytics
  constructor: (@$section) ->
    log "setting up instructor dashboard section - analytics"

    $display = @$section.find('.distribution-display')
    @$display_text  = $display.find('.distribution-display-text')
    @$display_graph = $display.find('.distribution-display-graph')
    @$display_table = $display.find('.distribution-display-table')
    @$distribution_select = @$section.find('select#distributions')

    @populate_selector => @$distribution_select.change => @on_selector_change()


  reset_display: ->
      @$display_text.empty()
      @$display_graph.empty()
      @$display_table.empty()


  populate_selector: (cb) ->
    @get_profile_distributions [], (data) =>
        @$distribution_select.find('option').eq(0).text "-- Select Distribution --"

        for feature in data.available_features
          opt = $ '<option/>',
            text: data.display_names[feature]
            data:
              feature: feature

          @$distribution_select.append opt

        cb?()


  on_selector_change: ->
    # log 'changeargs', arguments
    opt = @$distribution_select.children('option:selected')
    feature = opt.data 'feature'
    log "distribution selected: #{feature}"

    @reset_display()
    return unless feature
    @get_profile_distributions [feature], (data) =>
      feature_res = data.feature_results[feature]
      # feature response format: {'error': 'optional error string', 'type': 'SOME_TYPE', 'data': [stuff]}
      if feature_res.error
        console.warn(feature_res.error)
        @$display_text.text 'Error fetching data'
      else
        if feature_res.type is 'EASY_CHOICE'
          # setup SlickGrid
          options =
            enableCellNavigation: true
            enableColumnReorder: false

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
            datapoint[feature] = key
            datapoint['count'] = value
            datapoint

          table_placeholder = $ '<div/>', class: 'slickgrid'
          @$display_table.append table_placeholder
          grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
          grid.autosizeColumns()
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


  # handler can be either a callback for success or a mapping e.g. {success: ->, error: ->, complete: ->}
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


# exports
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Analytics: Analytics
