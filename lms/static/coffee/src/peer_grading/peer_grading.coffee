class PeerGrading
  constructor: (backend) ->
    @problem_list = $('.problem-list')
    @error_container = $('.error-container')
    @error_container.toggle(not @error_container.is(':empty'))


backend = {}
$(document).ready(() -> new PeerGrading(backend))
