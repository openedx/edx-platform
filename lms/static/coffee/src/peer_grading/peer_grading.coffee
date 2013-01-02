class PeerGrading
  constructor: (backend) ->
    @error_container = $('.error-container')
    @error_container.toggle(not @error_container.is(':empty'))

    @message_container = $('.message-container')
    @message_container.toggle(not @message_container.is(':empty'))

mock_backend = false
$(document).ready(() -> new PeerGrading(mock_backend))
