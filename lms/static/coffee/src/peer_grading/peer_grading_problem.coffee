class PeerGradingProblemBackend
  constructor: (ajax_url, mock_backend) ->
    @mock_backend = mock_backend

class PeerGradingProblem
  constructor: (backend) ->
    @error_container = $('.error-container')

    @render_problem()

  render_problem: () ->
    # do this when it makes sense
    @error_container.toggle(not @error_container.is(':empty'))


backend = {}
$(document).ready(() -> new PeerGradingProblem(backend))
