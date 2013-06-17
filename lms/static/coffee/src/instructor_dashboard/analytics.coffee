log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


class Analytics
  constructor: ($section) ->
    log "setting up instructor dashboard section - analytics"

    display = $section.find('.distribution-display')
    $display_text = display.find('.distribution-display-text')
    $display_graph = display.find('.distribution-display-graph')
    $display_table = display.find('.distribution-display-table')

    reset_display = ->
      $display_text.empty()
      $display_graph.empty()
      $display_table.empty()

    distribution_select = $section.find('select#distributions')

    # ask for available distributions
    $.getJSON distribution_select.data('endpoint'), features: JSON.stringify([]), (data) ->
        distribution_select.find('option').eq(0).text "-- Select distribution"

        for feature in data.available_features
          opt = $ '<option/>',
            text: data.display_names[feature]
            data:
              feature: feature

          distribution_select.append opt

        distribution_select.change ->
          opt = $(this).children('option:selected')
          log "distribution selected: #{opt.data 'feature'}"
          feature = opt.data 'feature'
          reset_display()
          $.getJSON distribution_select.data('endpoint'), features: JSON.stringify([feature]), (data) ->
            feature_res = data.feature_results[feature]
            # feature response format: {'error': 'optional error string', 'type': 'SOME_TYPE', 'data': [stuff]}
            if feature_res.error
              console.warn(feature_res.error)
              $display_text.text 'Error fetching data'
            else
              if feature_res.type is 'EASY_CHOICE'
                # $display_text.text JSON.stringify(feature_res.data)
                log feature_res.data

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

                log grid_data

                table_placeholder = $ '<div/>', class: 'slickgrid'
                $display_table.append table_placeholder
                grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
                grid.autosizeColumns()
              else if feature is 'year_of_birth'
                graph_placeholder = $ '<div/>', class: 'year-of-birth'
                $display_graph.append graph_placeholder

                graph_data = _.map feature_res.data, (value, key) -> [parseInt(key), value]
                log graph_data

                $.plot graph_placeholder, [
                  data: graph_data
                ]
              else
                console.warn("don't know how to show #{feature_res.type}")
                $display_text.text 'Unavailable Metric\n' + JSON.stringify(feature_res)


# exports
_.extend window, InstructorDashboard: {}
_.extend window.InstructorDashboard, sections: {}
_.extend window.InstructorDashboard.sections,
  Analytics: Analytics
