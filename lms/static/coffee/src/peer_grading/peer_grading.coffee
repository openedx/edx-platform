# This is a simple class that just hides the error container
# and message container when they are empty
# Can (and should be) expanded upon when our problem list 
# becomes more sophisticated
class PeerGrading
  constructor: () ->
    @error_container = $('.error-container')
    @error_container.toggle(not @error_container.is(':empty'))

    @message_container = $('.message-container')
    @message_container.toggle(not @message_container.is(':empty'))

$(document).ready(() -> new PeerGrading())
