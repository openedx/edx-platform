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
    setup_instructor_dashboard          instructor_dashboard_content
    setup_instructor_dashboard_sections instructor_dashboard_content


# enable navigation bar
# handles hiding and showing sections
setup_instructor_dashboard = (idash_content) =>
  # clickable section titles
  $links = idash_content.find(".#{CSS_INSTRUCTOR_NAV}").find('.btn-link')

  # attach link click handlers
  $links.each (i, link) ->
    $(link).click (e) ->
      e.preventDefault()

      # deactivate all link & section styles
      idash_content.find(".#{CSS_INSTRUCTOR_NAV} li").children().removeClass CSS_ACTIVE_SECTION
      idash_content.find(".#{CSS_INSTRUCTOR_NAV} li").children().attr('aria-pressed', 'false')
      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION

      # discover section paired to link
      section_name = $(this).data 'section'
      $section = idash_content.find "##{section_name}"

      # activate link & section styling
      $(this).addClass CSS_ACTIVE_SECTION
      $(this).attr('aria-pressed','true')
      $section.addClass CSS_ACTIVE_SECTION

      # tracking
      analytics.pageview "instructor_section:#{section_name}"

      # deep linking
      # write to url
      location.hash = "#{HASH_LINK_PREFIX}#{section_name}"

      sections_have_loaded.after ->
        $section.data('wrapper').onClickTitle()

      # call onExit handler if exiting a section to a different section.
      unless $section.is $active_section
        $active_section?.data('wrapper')?.onExit?()
      $active_section = $section

      # TODO enable onExit handler


  # activate an initial section by 'clicking' on it.
  # check for a deep-link, or click the first link.
  click_first_link = ->
    link = $links.eq(0)
    link.click()

  if (new RegExp "^#{HASH_LINK_PREFIX}").test location.hash
    rmatch = (new RegExp "^#{HASH_LINK_PREFIX}(.*)").exec location.hash
    section_name = rmatch[1]
    link = $links.filter "[data-section='#{section_name}']"
    if link.length == 1
      link.click()
    else
      click_first_link()
  else
    click_first_link()



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
