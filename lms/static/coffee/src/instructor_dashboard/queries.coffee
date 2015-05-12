###
Queries Section
imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

class EmailSelectors
  DESCRIPTION_LIMIT : 50
  TRUNCATION : 60

  constructor: (@$container, $section, params={}) ->
    params = _.defaults params,
      label : @$container.data('label')

    templateHtml = $('#email-list-widget-template').html()
    @$container.html Mustache.render templateHtml, params
    labelArray = (@$container.data('selections')).split '<>'
    @$listSelector = @$container.find('select.single-email-selector')
    # populate selectors
    @$listSelector.empty()
    @listEndpoint = @$container.data('list-endpoint')
    @$listSelector.append($('<option/>'))
    if $container.attr('data-label') == 'Select Section'
      @load_list()
    else if @$container.attr('data-label') == 'Select Problem'
      @load_list()
    else
      for label in labelArray
        @$listSelector.append($('<option/>',
          text: label
          )
        )

    @$listSelector.change =>
      $opt = @$listSelector.children('option:selected')
      if (!$opt.length)
        return
      if @$container.attr('data-label') == gettext('Select a Type')
        chosenClass = $opt.text().trim()
        if (chosenClass == 'Section')
          $section.find('.problem_specific').removeClass('active')
          $section.find('.section_specific').addClass('active')
        else if (chosenClass == 'Problem')
          $section.find('.section_specific').removeClass('active')
          $section.find('.problem_specific').addClass('active')

  get_list: (cb) ->
    $.ajax(
      dataType: 'json'
      url: @listEndpoint
      success: (data) -> cb? null, data['data']
      error: std_ajax_err ->
        cb? gettext('Error fetching problem or section data')
    )

  # load section/problem data
  load_list: ->
    @get_list (error, section_list) =>
      # abort on error
      if error
        return @show_errors error
      _.each section_list, (section) =>
        @add_row(section, 'section')
        _.each section.sub, (subsection) =>
          @add_row(subsection , 'subsection')

  add_row: (node, sectionOrSubsection) ->
    idArr = [node.block_type, node.block_id]
    idSt = idArr.join('/')
    toDisplay = node.display_name
    if node.parents
      toDisplay = [node.parents, toDisplay].join('<>')
    # indenting subsections with dashes for readability
    if sectionOrSubsection == 'subsection'
      toDisplay = '---' + toDisplay
    if toDisplay.length > @DESCRIPTION_LIMIT
      # displaying the last n characters
      toDisplay = '...' + toDisplay.substring(Math.max(0,toDisplay.length - @TRUNCATION), toDisplay.length)
    @$listSelector.append($('<option/>',
            text: toDisplay
            class: sectionOrSubsection
            id: idSt
      ))

class EmailWidget
  constructor:  (emailLists, $section, @$emailListContainers, @$error_section)  ->
    @$queryEndpoint = $('.email-lists-management').data('query-endpoint')
    @$totalEndpoint = $('.email-lists-management')
      .data('total-endpoint')
    @$deleteSavedEndpoint = $('.email-lists-management')
      .data('delete-saved-endpoint')
    @$deleteTempEndpoint = $('.email-lists-management')
      .data('delete-temp-endpoint')
    @$deleteBatchTempEndpoint = $('.email-lists-management')
      .data('delete-batch-temp-endpoint')
    for emailList in emailLists
      emailList.$container.addClass('active')

    @$getEstBtn = $section.find("input[name='getest']")
    @$getEstBtn.click () =>
      @reload_estimated()

    @$startoverBtn = $section.find("input[name='startover']")
    @$startoverBtn.click () =>
      @delete_temporary()
      $('.emailWidget.queryTableBody tr').remove()
      @reload_estimated()

    @$saveQueryBtn = $section.find("input[name='savequery']")
    @$saveQueryBtn.click () =>
      @send_save_query()

    @$emailCsvBtn = $section.find("input[name='getcsv']")
    @$emailCsvBtn.click (event) =>
      rows = $('.emailWidget.queryTableBody tr')
      sendingQuery = _.map (rows), (row) =>
          row.getAttribute('query')
      sendData = sendingQuery.join(',')
      url = @$emailCsvBtn.data('endpoint')
      # handle csv special case
      # redirect the document to the csv file.
      url += '/csv'
      url += '?existing=' + window.encodeURIComponent(sendData)
      window.location.href = url

    @load_saved_queries()
    @load_saved_temp_queries()
    POLL_INTERVAL_IN_MS = 15000 # 15 * 1000, 15 seconds in ms
    @poller = new window.InstructorDashboard.util.IntervalManager(
      POLL_INTERVAL_IN_MS, => @load_saved_temp_queries()
    )

    $('.emailWidget.addQuery').click (event) =>
      $selected = @$emailListContainers.find('select.single-email-selector option:selected')
        #.children('option:selected')
      # check to see if stuff has been filled out
      if $selected[1].text == 'Section'
        selectedOptions = [{'text':$selected[0].text, 'id':$selected[0].id},
                {'text':$selected[1].text, 'id':$selected[1].id},
                {'text':$selected[4].text, 'id':$selected[4].id},
                {'text':$selected[5].text, 'id':$selected[5].id}]
        selectedOptionsText = [$selected[0].text, $selected[1].text,
                     $selected[4].text, $selected[5].text]
      else
        selectedOptions = [{'text':$selected[0].text, 'id':$selected[0].id},
                {'text':$selected[1].text, 'id':$selected[1].id},
                {'text':$selected[2].text, 'id':$selected[2].id},
                {'text':$selected[3].text, 'id':$selected[3].id}]
        selectedOptionsText = [$selected[0].text, $selected[1].text,
                     $selected[2].text, $selected[3].text]

      for option in selectedOptions
        if option['text'] == ''
          $('.emailWidget.incompleteMessage').html(gettext('Query is incomplete. Please make all the selections.'))
          return

      $('.emailWidget.incompleteMessage').html('')
      @chosen = $selected[0].text
      @tr = @start_row(@chosen.toLowerCase(), selectedOptions, '', $('.emailWidget.queryTableBody'))
      @useQueryEndpoint = [
          @$queryEndpoint,
          selectedOptionsText.slice(0,2).join('/'),
          selectedOptions[2].id
      ].join('/')
      @filtering = selectedOptions[3].text
      @entityName = selectedOptions[2].text
      @reload_students(@tr)
      @$emailListContainers.find('select.single-email-selector').
        prop('selectedIndex', 0)
      $('.problem_specific').removeClass('active')
      $('.section_specific').removeClass('active')

  get_saved_temp_queries: (cb) ->
    $.ajax(
      dataType: 'json'
      url: $('.email-lists-management').data('temp-queries-endpoint')
      success: (data) -> cb? null, data
      error: std_ajax_err ->
        cb? gettext('Error getting saved temp queries')
    )

  # get a user's in-progress queries and load them into active queries
  load_saved_temp_queries: ->
    @get_saved_temp_queries (error, data) =>
      # abort on error
      if error
        return @show_errors error
      $('.emailWidget.queryTableBody tr').remove()
      queries = data['queries']
      # use _.each instead of 'for' so that member
      # is bound in the button callback.
      _.each queries, (query) =>
        queryId = query['id']
        blockId = query['block_id']
        blockType = query['block_type']
        stateKey = blockType + '/' + blockId
        displayName = query['display_name']
        displayEntity = {'text':displayName, 'id':stateKey}
        filterOn = {'text':query['filter_on']}
        inclusion = {'text':query['inclusion']}
        done = query['done']
        type = {'text':query['type']}
        arr = [inclusion, type, displayEntity, filterOn, done]
        @tr = @start_row(inclusion['text'].toLowerCase(),arr,
          {'class':['working'],'query':queryId},  $('.emailWidget.queryTableBody'))
        @check_done()

  get_saved_queries: (cb) ->
    $.ajax(
      dataType: 'json'
      url: $('.emailWidget.savedQueriesTable').data('endpoint')
      success: (data) -> cb? null, data
      error: std_ajax_err ->
        cb? gettext('Error getting saved queries')
    )
  # get a user's saved queries and load them into saved queries
  load_saved_queries: ->
    $('.emailWidget.savedQueriesTable tr').remove()
    $('.emailWidget.invisibleQueriesStorage tr').remove()
    @get_saved_queries (error, data) =>
      # abort on error
      if error
        return @show_errors error
      queries = data['queries']
      groups = new Set()
      groupNames = {}
      invisibleTable = $('.emailWidget.invisibleQueriesStorage')
      _.each queries, (query) =>
        blockId = query['block_id']
        blockType = query['block_type']
        stateKey = blockType + '/' + blockId
        displayName = query['display_name']
        displayEntity = {'text':displayName, 'id':stateKey}
        filterOn = {'text':query['filter_on']}
        inclusion = {'text':query['inclusion']}
        created = query['created']
        type = {'text':query['type']}
        queryVals = [inclusion, type, displayEntity, filterOn]
        @tr = @start_row(inclusion['text'], queryVals,
          {'class':['saved' + query.group]}, invisibleTable)
        @tr[0].setAttribute('created',created)
        groups.add(query['group'])
        if query['group_title'].length != 0
          groupNames[query['group']] = query['group_title']
      savedGroup = []
      iter = groups.values()
      val = iter.next()
      while (val['done'] == false)
        savedGroup.push(val['value'])
        val = iter.next()
      savedGroup.sort((a, b) ->return b-a)
      for group in savedGroup
        lookup = '.saved' + group
        savedQs = $(lookup)
        types = []
        names = []
        time = ''
        for query in savedQs
          cells = query.children
          types.push(jQuery(cells[0]).text())
          names.push(jQuery(cells[2]).text())
          time = query.getAttribute('created')
        if typeof groupNames[group] == 'undefined'
          savedQueryDisplayName = ''
          for i in [0..types.length-1]
            savedQueryDisplayName += types[i]
            savedQueryDisplayName += ' '
            savedQueryDisplayName += names[i] + ' '
        else
          savedQueryDisplayName = groupNames[group]
        savedVals = [{'text': time}, {'text': savedQueryDisplayName}]
        @start_saved_row('and', savedVals, group, $('.emailWidget.savedQueriesTable'))

  # if each individual query is processed, allow the user
  # to download the csv and save the query
  check_done: ->
    # check if all other queries have returned, if so can get total csv
    rowArr = []
    tab = $('.emailWidget.queryTableBody')
    rows = tab.find('tr')
    _.each rows, (row) ->
      rowArr.push(row.getAttribute('query'))
    allGood = true
    _.each (rowArr), (status) ->
      if status == 'working'
        allGood = false
    if allGood
      @$saveQueryBtn.removeClass('disabled')
      @$emailCsvBtn.removeClass('disabled')
      @$emailCsvBtn[0].value = 'Download CSV'

  # deletes an active query from the table and the db
  delete_temporary:->
    queriesToDelete = []
    _.each $('.emailWidget.queryTableBody tr'), (row) ->
      if row.hasAttribute('query')
        queryToDelete = row.getAttribute('query')
        queriesToDelete.push(queryToDelete)
    @delete_temp_query_batch(queriesToDelete)
    $('.emailWidget.queryTableBody tr').remove()

  rename_button_click:(event) ->
    $saveCancelEditButton = $ _.template('<div class="emailWidget saveEditName"><i class="fa icon fa-floppy-o"></i>
          <%= labelSave %></div> <div class="emailWidget cancelEditName"><i class="fa icon fa-times-circle">
          </i> <%= labelCancel %></div>', {labelSave: 'Save' ,labelCancel: 'Cancel' })
    $renameBtn = $ _.template('<div class="emailWidget editName"><i class="icon fa fa-pencil">
      </i> <%= label %></div>', {label: 'Rename'})
    targ = event.target
    while (!targ.classList.contains('editName'))
        targ = targ.parentNode
    targ = jQuery(targ).parent()
    originalText = targ.text().trim().substring(6)
    targ.html('');
    targ.append($saveCancelEditButton)
    htmlString = '<div class="emailWidget invisibleSavedGroupName">'+
      originalText+'</div><input type="text" class="emailWidget editNameInput" name="queryName" value="'+originalText+'">'
    targ.append(htmlString)
    $cancelEditButton = targ.find(".emailWidget.cancelEditName")
    $saveEditButton = targ.find(".emailWidget.saveEditName")
    $cancelEditButton.click (event) =>
      targ = event.target
      while (!targ.classList.contains('cancelEditName'))
        targ = targ.parentNode
      targ = jQuery(targ)
      parent = targ.parent()
      originalText = parent.find(".emailWidget.invisibleSavedGroupName").text()
      parent.html('')
      parent.append($renameBtn)
      parent.append(originalText)
      $renameBtn.click (event) =>
        @rename_button_click(event)
    $saveEditButton.click (event) =>
      targ = event.target
      while (!targ.classList.contains('saveEditName'))
        targ = targ.parentNode
      targ = jQuery(targ)
      parent = targ.parent()
      inputField = parent.find(".emailWidget.editNameInput")
      newGroupName = inputField.attr("value")
      groupId = parent.parent().attr("groupquery")
      send_data =
        group_id: groupId
        group_name: newGroupName
      $.ajax(
        type: 'POST'
        dataType: 'json'
        url: $('.emailWidget.savedQueriesTable').data('group-name-endpoint')
        data: send_data
        success: $('#send_email select option[value="' +groupId + '"]').text(newGroupName)
        error: std_ajax_err ->
          cb? gettext('Error saving group name')
      )
      newText = newGroupName
      parent.html('')
      parent.append($renameBtn)
      parent.append(newText)
      $renameBtn.click (event) =>
        @rename_button_click(event)

  # adds a row to saved queries
  start_saved_row:(color, arr, id, table) ->
    # find which row to insert in
    rows = table[0].children
    row = table[0].insertRow(rows)
    row.setAttribute('groupQuery', id)
    $renameBtn = $ _.template('<div class="emailWidget editName"><i class="icon fa fa-pencil">
      </i> <%= label %></div>', {label: 'Rename'})
    for num in [0..1]
      cell = row.insertCell(num)
      item = arr[num]
      if num == 1
        $(cell).append($renameBtn)
      $(cell).append(item['text'])
      if item.hasOwnProperty('id')
        cell.id = item['id']

    $renameBtn.click (event) =>
      @rename_button_click(event)

    $loadBtn = $ _.template('<div class="loadQuery"><i class="icon fa fa-upload">
      </i> <%= label %></div>', {label: 'Load'})
    $loadBtn.click (event) =>
      @delete_temporary()
      $('.emailWidget.queryTableBody tr').remove()
      targ = event.target
      while (!targ.classList.contains('loadQuery'))
        targ = targ.parentNode
      curRow = targ.parentNode.parentNode
      groupedQueryId = curRow.getAttribute('groupQuery')
      @$emailCsvBtn[0].value = gettext('Aggregating Queries')
      $('.emailWidget.incompleteMessage').html('')
      rowsToAdd = $('.saved' + groupedQueryId)
      for row in rowsToAdd
        cells = row.children
        savedQueryOptions = [{'text': jQuery(cells[0]).text()},
                {'text': jQuery(cells[1]).text()},
                {'text': jQuery(cells[2]).text(), 'id':cells[2].id},
                {'text': jQuery(cells[3]).text()}]

        savedQueryOptionsText = [jQuery(cells[0]).text(), jQuery(cells[1]).text(),
                     jQuery(cells[2]).text(), jQuery(cells[3]).text()]
        @tr = @start_row( jQuery(cells[0]).text().toLowerCase(),
          savedQueryOptions,'', $('.emailWidget.queryTableBody'))
        # todo:this feels too hacky. suggestions?
        @useQueryEndpoint = [
          @$queryEndpoint,
          savedQueryOptionsText.slice(0,2).join('/'),
          savedQueryOptions[2].id
        ].join('/')
        @filtering = savedQueryOptions[3].text
        @entityName = savedQueryOptions[2].text
        @reload_students(@tr)
        @$emailListContainers.find('select.single-email-selector').
          prop('selectedIndex',0)
        $('.problem_specific').removeClass('active')
        $('.section_specific').removeClass('active')
    $td = $('<td>')
    $td.append($loadBtn)
    row.appendChild($td[0])
    $deleteBtn = $(_.template('<div class="deleteSaved">
      <i class="icon fa fa-times-circle"></i> <%= label %></div>', {label: 'Delete'}))

    $deleteBtn.click (event) =>
      targ = event.target
      while (!targ.classList.contains('deleteSaved'))
        targ = targ.parentNode
      curRow = targ.parentNode.parentNode
      curRow.remove()
      queryToDelete = curRow.getAttribute('groupquery')
      @delete_saved_query(queryToDelete)
      $('#send_email option[value="' + queryToDelete + '"]').remove()
    $td = $('<td>')
    $td.append($deleteBtn)
    row.appendChild($td[0])
    return $(row)

  get_students: (cb) ->
    tab = $('.emailWidget.queryTableBody')
    rows = tab.find('tr')
    _.each rows, (row) ->
      type = row.classList[0]
      problems = []
      _.each row.children, (child) ->
        id = child.id
        html = child.innerHTML
        problems.push({'id': id, 'text': html})
      problems = problems.slice(0, -1)
    send_data =
      filter: @filtering
      entityName: @entityName
    $.ajax
      dataType: 'json'
      url: @useQueryEndpoint
      data: send_data
      success: (data) -> cb? null, data
      error: std_ajax_err ->
        cb? gettext('Error getting students')

  # make a single query to the backend. doesn't wait for
  # query completion as that can take awhile
  reload_students: (tr) ->
    @$saveQueryBtn.addClass('disabled')
    @$emailCsvBtn.addClass('disabled')
    @$emailCsvBtn[0].value = gettext('Aggregating Queries')
    tr.addClass('working')
    @get_students (error, students) =>
      if error
        $broken_icon = $ _.template('<div class="done">
          <i class="icon fa fa-exclamation-triangle"></i> <%= label %></div>',
          {label: gettext("Sorry, we're having a problem with this query.
            Please delete this row and try again.")})
        tr.children()[4].innerHTML = $broken_icon[0].outerHTML
        return @show_errors error

  # we don't care if these calls succeed or not so no wrapped callback
  delete_temp_query: (queryId) ->
    $.ajax(
      type: 'POST'
      dataType: 'json'
      url: @$deleteTempEndpoint
      data: "query_id": queryId
    )

  delete_temp_query_batch: (queryIds) ->
    sendData =
      existing: queryIds.join(',')
    $.ajax(
      type: 'POST'
      dataType: 'json'
      url: @$deleteBatchTempEndpoint
      data: sendData
    )

  delete_saved_query: (queryId) ->
    $.ajax(
      type: 'POST'
      dataType: 'json'
      url:  @$deleteSavedEndpoint
      data: "query_id": queryId
    )

  # adds a row to active queries
  start_row:(color, arr, rowIdClass, table) ->
    # find which row to insert in
    idx =0
    orIdx = 0
    andIdx = 0
    notIdx = 0
    useIdx = 0
    rows = table[0].children
    # figuring out where to place the new row
    # we want the group order to be and, or, not
    for curRow in rows
      idx += 1
      if curRow.classList.contains('or')
        orIdx = idx
      if curRow.classList.contains('and')
        andIdx = idx
      if curRow.classList.contains('not')
        notIdx = idx
      if curRow.classList.contains(color)
        useIdx = idx
    if color == 'or' and useIdx == 0
      useIdx = Math.max(notIdx, andIdx)
    if color == 'not' and useIdx == 0
      useIdx =andIdx
    row = table[0].insertRow(useIdx)
    if rowIdClass.hasOwnProperty('id')
      row.id = rowIdClass['id']
    if rowIdClass.hasOwnProperty('query')
      row.setAttribute('query',rowIdClass['query'])

    row.classList.add(color.toLowerCase())
    if rowIdClass.hasOwnProperty('class')
      _.each rowIdClass['class'], (addingClass) ->
        row.classList.add(addingClass.toLowerCase())
    for num in [0..3]
      cell = row.insertCell(num)
      item = arr[num]
      cell.innerHTML = item['text']
      if item.hasOwnProperty('id') and item['id'] !=''
        cell.id = item['id']
    progressCell = row.insertCell(4)
    $progress_icon = $ _.template('<div class="Working">
      <i class="fa fa-spinner fa-spin"></i><%= label %></div>',
      {label: 'Working'})
    $done_icon = $ _.template('<div class="done"><i class="icon fa fa-check">
      </i> <%= label %></div>', {label: 'Done'})
    $broken_icon = $ _.template('<div class="done">
      <i class="icon fa fa-exclamation-triangle"></i> <%= label %></div>',
      {label: gettext("Sorry, we're having a problem with this query.
        Please delete this row and try again.")})
    if arr.length == 4
      progressCell.innerHTML = $progress_icon[0].outerHTML
    else
      if arr[4] == null
        progressCell.innerHTML = $broken_icon[0].outerHTML
      else if arr[4] == true
        progressCell.innerHTML = $done_icon[0].outerHTML
        row.classList.remove('working')
      else
        progressCell.innerHTML = $progress_icon[0].outerHTML
    $removeBtn = $(_.template('<div class="remove"><i class="icon fa fa-times-circle">
      </i> <%= label %></div>', {label: 'Remove'}))
    $removeBtn.click (event) =>
      targ = event.target
      while (!targ.classList.contains('remove'))
        targ = targ.parentNode
      curRow = targ.parentNode.parentNode
      curRow.remove()
      if curRow.hasAttribute('query')
        queryToDelete = curRow.getAttribute('query')
        @delete_temp_query(queryToDelete)
      @check_done()
    $td = $ '<td>'
    $td.append($removeBtn)
    row.appendChild($td[0])
    return $(row)

  save_query: (cb)->
    cur_queries = []
    tab = $('.emailWidget.queryTableBody')
    rows = tab.find('tr')
    _.each rows, (row) ->
      cur_queries.push(row.getAttribute('query'))
    send_data =
      existing: cur_queries.join(',')
      savedName: $(".emailWidget.savequeryname").val()
    $(".emailWidget.savequeryname").val("")
    $.ajax(
      type: 'POST'
      dataType: 'json'
      url: @$saveQueryBtn.data('endpoint')
      data: send_data
      success: (data) -> cb? null, data
      error: std_ajax_err ->
        cb? gettext('Error saving query')
    )
  # save queries in active queries
  send_save_query: ->
    @save_query (error, data) =>
      if error
        return @show_errors error
      $('#send_email select').append('<option value="' + data['group_id'] + '">' + data['group_title'] + '</option>')
      @load_saved_queries()

  get_estimated: (cb)->
    curQueries = []
    tab = $('.emailWidget.queryTableBody')
    rows = tab.find('tr')
    _.each rows, (row) ->
      curQueries.push(row.getAttribute('query'))
    send_data =
      existing: curQueries.join(',')
    $.ajax
      dataType: 'json'
      url: @$totalEndpoint
      data: send_data
      success: (data) -> cb? null, data
      error: std_ajax_err ->
        cb? gettext('Error getting estimated')

  # estimate the students selected
  reload_estimated: ->
    $('.emailWidget.estimated').html(gettext('Calculating'))
    @get_estimated (error, students) =>
      if students['success'] == false
        $('.emailWidget.estimated').html(gettext('0 students selected'))
        return
      studentsList = students['data']
      queryId = students['query_id']
      # abort on error
      if error
        return @show_errors error
      $numberStudents = studentsList.length
      $('.emailWidget.estimated').html(gettext('approx ' + $numberStudents + ' students selected'))
  # set error display
  show_errors: (msg) -> @$error_section?.text msg

#Queries Section
class Queries
  # enable subsections.
  constructor: (@$section) ->
    # attach self to html
    # so that instructor_dashboard.coffee can find this object
    # to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    #initialize email widget selectors
    @$emailListContainers = @$section.find('.email-list-container')
    @emailLists = _.map (@$emailListContainers), (email_list_container) =>
      new EmailSelectors $(email_list_container), @$section
    @$email_widget_errors = @$section.find '.email-lists-management .request-response-error'
    #initialize email widget
    @widget = new EmailWidget(@emailLists, @$section, @$emailListContainers, @$email_widget_errors)

  # handler for when the section title is clicked.
  onClickTitle: ->
    # Clear display of anything that was here before
    @$email_widget_errors?.text('')
    # poll for query status every 15 seconds
    @widget.poller.start()

  # handler for when the section is closed
  onExit: ->
    @widget.poller.stop()
    # Clear any generated tables, warning messages, etc.
    @$email_widget_errors?.text('')
# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  Queries: Queries
