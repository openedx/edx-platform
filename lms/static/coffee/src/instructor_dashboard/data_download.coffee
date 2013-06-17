log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


class DataDownload
  constructor: (@$section) ->
    log "setting up instructor dashboard section - data download"

    $display = @$section.find('.data-display')
    @$display_text  = $display.find('.data-display-text')
    @$display_table = $display.find('.data-display-table')

    $list_studs_btn = @$section.find("input[name='list-profiles']'")
    $list_studs_btn.click (e) =>
      log "fetching student list"
      url = $list_studs_btn.data('endpoint')
      if $(e.target).data 'csv'
        url += '/csv'
        location.href = url
      else
        @reset_display()
        $.getJSON url, (data) =>
          # setup SlickGrid
          options =
            enableCellNavigation: true
            enableColumnReorder: false

          columns = ({id: feature, field: feature, name: feature} for feature in data.queried_features)
          grid_data = data.students

          $table_placeholder = $ '<div/>', class: 'slickgrid'
          @$display_table.append $table_placeholder
          grid = new Slick.Grid($table_placeholder, grid_data, columns, options)
          grid.autosizeColumns()

    $grade_config_btn = @$section.find("input[name='dump-gradeconf']'")
    $grade_config_btn.click (e) =>
      log "fetching grading config"
      url = $grade_config_btn.data('endpoint')
      $.getJSON url, (data) =>
        @reset_display()
        @$display_text.html data['grading_config_summary']


  reset_display: ->
    @$display_text.empty()
    @$display_table.empty()


# exports
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  DataDownload: DataDownload
