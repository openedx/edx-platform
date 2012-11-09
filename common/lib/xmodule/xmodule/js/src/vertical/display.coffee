class @Vertical
  constructor: (element) ->
    @el = $(element).find('.vert-wrapper')
    @hookUpProgressEvent()
    @updateProgress()
 
   hookUpProgressEvent: ->
    $('.problems-wrapper').bind 'progressChanged', @updateProgress

  mergeProgressStatus: (p1, p2) ->
    # if either is "NA", return the other one
    if p1 == "NA"
      return p2
    if p2 == "NA"
      return p1

    # Both real progresses
    if p1 == "done" and p2 == "done"
      return "done"

    # not done, so if any progress on either, in_progress
    w1 = p1 == "done" or p1 == "in_progress"
    w2 = p2 == "done" or p2 == "in_progress"
    if w1 or w2
      return "in_progress"

    return "none"

  updateOverallScore: (details, status) =>
    # Given a list of "a/b" strings, compute the sum(a)/sum(b), and the corresponding percentage
    gotten = 0
    possible = 0
    for d in details
      if d? and d.indexOf('/') > 0
        a = d.split('/')
        got = parseInt(a[0])
        pos = parseInt(a[1])
        gotten += got
        possible += pos

    # only output an overall score if there were some possible:
    if possible > 0
      status_msg = ""
      score = ""
      if status == "none"
        status_msg = "(Not Started)"
        score = "(" + possible + " points possible)"
      else
        status_msg = (gotten / possible * 100).toFixed(1) + "%"
        score = " (" + gotten + '/' + possible + " points)"
      @el.find('.vert-progress-status').html(status_msg)
      @el.find('.vert-progress-score').html(score)
      

  updateProgress: =>
    # check to see if there is any progress to maintain at all
    problems = $('.problems-wrapper')
    if problems.length == 0
      @el.find('.vert-progress').addClass('hidden')
      return
    # we have some problems to update  
    new_progress_status = "NA"
    details = []
    _this = this
    # $('.problems-wrapper').each (index) ->
    problems.each (index) ->
      progress_status = $(this).data('progress_status')
      new_progress_status = _this.mergeProgressStatus progress_status, new_progress_status

      progress_detail = $(this).data('progress_detail')
      details.push(progress_detail)

    @updateOverallScore(details, new_progress_status)


