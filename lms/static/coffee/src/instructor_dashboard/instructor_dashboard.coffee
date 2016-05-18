###
Instructor Dashboard Tab Manager

The instructor dashboard is broken into sections.

Only one section is visible at a time,
  and is responsible for its own functionality.

NOTE: plantTimeout (which is just setTimeout from util.coffee)
      is used frequently in the instructor dashboard to isolate
      failures. If one piece of code under a plantTimeout fails
      then it will not crash the rest of the dashboard.

NOTE: The instructor dashboard currently does not
      use backbone. Just lots of jquery. This should be fixed.

NOTE: Server endpoints in the dashboard are stored in
      the 'data-endpoint' attribute of relevant html elements.
      The urls are rendered there by a template.

NOTE: For an example of what a section object should look like
      see course_info.coffee

imports from other modules
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# CSS classes
CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'
CSS_INSTRUCTOR_NAV = 'instructor-nav'

# prefix for deep-linking
HASH_LINK_PREFIX = '#view-'

$active_section = null

# tab variables for keystrokes
KEYS = {
    'left':     37,
    'right':    39,
    'down':     40,
    'up':       38
}

# helper class for queueing and fault isolation.
# Will execute functions marked by waiter.after only after all functions marked by
# waiter.waitFor have been called.
# To guarantee this functionality, waitFor and after must be called
# before the functions passed to waitFor are called.
class SafeWaiter
  constructor: ->
    @after_handlers = []
    @waitFor_handlers = []
    @fired = false

  after: (f) ->
    if @fired
      f()
    else
      @after_handlers.push f

  waitFor: (f) ->
    return if @fired
    @waitFor_handlers.push f

    # wrap the function so that it notifies the waiter
    # and can fire the after handlers.
    =>
      @waitFor_handlers = @waitFor_handlers.filter (g) -> g isnt f
      if @waitFor_handlers.length is 0
        @fired = true
        @after_handlers.map (cb) -> plantTimeout 0, cb

      f.apply this, arguments


# waiter for dashboard sections.
# Will only execute after all sections have at least attempted to load.
# This is here to facilitate section constructors isolated by setTimeout
# while still being able to interact with them under the guarantee
# that the sections will be initialized at call time.
sections_have_loaded = new SafeWaiter

# once we're ready, check if this page is the instructor dashboard
$ =>
  instructor_dashboard_content = $ ".#{CSS_INSTRUCTOR_CONTENT}"
  if instructor_dashboard_content.length > 0
    setup_instructor_dashboard_sections instructor_dashboard_content
    tabs()
    true

# proper tabpanel handling for the dashboard
tabs = () ->
    startTab = $('.' + CSS_INSTRUCTOR_NAV).children('.nav-item').first()
    startPanel = $(startTab).attr('aria-controls')
    
    checkForLocationHash(startTab, startPanel)
    
    keyListener()
    clickListener()
    
resetTabs = () ->
    $('.'+ CSS_INSTRUCTOR_NAV).children('.nav-item').each (index, element) ->
        tab = $(element)
        $(tab).attr({ 'aria-selected': 'false', 'tabindex': '-1' }).removeClass CSS_ACTIVE_SECTION
    
    resetTabPanels()
    
resetTabPanels = () ->
    $('.' + CSS_IDASH_SECTION).each (index, element) =>
        panel = $(element)
        $(panel).attr({ 'aria-hidden': 'true', 'tabindex': '-1' }).hide().removeClass CSS_ACTIVE_SECTION

keyListener = () ->
    $('.' + CSS_INSTRUCTOR_NAV).on 'keydown', '.nav-item', (event) =>
        key = event.which
        focused = $(event.currentTarget)
        index = $(focused).parent().find('.nav-item').index(focused)
        total = $(focused).parent().find('.nav-item').size() - 1
        panel = $(focused).attr('aria-controls')
        
        switch key
            when KEYS.left, KEYS.up then previousTab(focused, index, total, event)
            when KEYS.right, KEYS.down then nextTab(focused, index, total, event)
            else return
    
clickListener = () ->
    $('.' + CSS_INSTRUCTOR_NAV).on 'click', '.nav-item', (event) ->
        tab = $(event.currentTarget)
        panel = $(tab).attr('aria-controls')
        
        resetTabs()
        activateTab(tab, panel)
        
previousTab = (focused, index, total, event) ->
    if (event.altKey || event.shiftKey)
        true
    if (index == 0)
        tab = $(focused).parent().find('.nav-item').last()
    else
        tab = $(focused).parent().find('.nav-item:eq(' + index + ')').prev()

    panel = $(tab).attr('aria-controls')
    
    $(tab).focus()
    activateTab(tab, panel)
    false
    
nextTab = (focused, index, total, event) ->
    if (event.altKey || event.shiftKey)
        true
    if (index == total)
        tab = $(focused).parent().find('.nav-item').first()
    else
        tab = $(focused).parent().find('.nav-item:eq(' + index + ')').next()

    panel = $(tab).attr('aria-controls')
    
    $(tab).focus()
    activateTab(tab, panel)
    false

activateTab = (tab, panel) ->
    resetTabs()
    activateTabPanel(panel)
    
    section_name = $(tab).data 'section'
    
    $(tab).attr({ 'aria-selected': 'true', 'tabindex': '0' }).addClass CSS_ACTIVE_SECTION
    
    tabAnalytics(section_name)
    updateLocationHash(section_name)
    
activateTabPanel = (panel) ->
    resetTabPanels()
    
    $('#' + panel).attr({ 'aria-hidden': 'false', 'tabindex': '0' }).show().addClass CSS_ACTIVE_SECTION
      
updateLocationHash = (section_name) ->
    # deep linking, writing url
    location.hash = "#{HASH_LINK_PREFIX}#{section_name}"
    
checkForLocationHash = (startTab, startPanel) ->
    # if sent a deep link, activate appropriate page section
    if (location.hash)
        if (new RegExp "^#{HASH_LINK_PREFIX}").test location.hash
            rmatch = (new RegExp "^#{HASH_LINK_PREFIX}(.*)").exec location.hash
            section_name = rmatch[1]
            link = $('.' + CSS_INSTRUCTOR_NAV + ' .nav-item').filter "[data-section='#{section_name}']"
            panel = $(link).attr('aria-controls')
        if link.length == 1
            activateTab(link, panel)
        else
            activateTab(startTab, startPanel)
    else
        activateTab(startTab, startPanel)
    
tabAnalytics = (section_name) ->
    analytics.pageview "instructor_section:#{section_name}"

# enable sections
setup_instructor_dashboard_sections = (idash_content) ->
  sections_to_initialize = [
    constructor: window.InstructorDashboard.sections.CourseInfo
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#course_info"
  ,
    constructor: window.InstructorDashboard.sections.DataDownload
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#data_download"
  ,
    constructor: window.InstructorDashboard.sections.ECommerce
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#e-commerce"
  ,
    constructor: window.InstructorDashboard.sections.Membership
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#membership"
  ,
    constructor: window.InstructorDashboard.sections.StudentAdmin
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#student_admin"
  ,
    constructor: window.InstructorDashboard.sections.Extensions
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#extensions"
  ,
    constructor: window.InstructorDashboard.sections.Email
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#send_email"
  ,
    constructor: window.InstructorDashboard.sections.InstructorAnalytics
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#instructor_analytics"
  ,
    constructor: window.InstructorDashboard.sections.Metrics
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#metrics"
  ,
    constructor: window.InstructorDashboard.sections.CohortManagement
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#cohort_management"
  ,
    constructor: window.InstructorDashboard.sections.Certificates
    $element: idash_content.find ".#{CSS_IDASH_SECTION}#certificates"
  ]
  # proctoring can be feature disabled
  if edx.instructor_dashboard.proctoring != undefined
    sections_to_initialize = sections_to_initialize.concat [
      constructor: edx.instructor_dashboard.proctoring.ProctoredExamAllowanceView
      $element: idash_content.find ".#{CSS_IDASH_SECTION}#special_exams"
    ,
      constructor: edx.instructor_dashboard.proctoring.ProctoredExamAttemptView
      $element: idash_content.find ".#{CSS_IDASH_SECTION}#special_exams"
    ]

  sections_to_initialize.map ({constructor, $element}) ->
    # See fault isolation NOTE at top of file.
    # If an error is thrown in one section, it will not stop other sections from exectuing.
    plantTimeout 0, sections_have_loaded.waitFor ->
      new constructor $element
