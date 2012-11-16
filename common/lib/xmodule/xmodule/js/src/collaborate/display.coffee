class @FindCollaborator
  constructor: (element) ->
    @socket = io.connect('http://127.0.0.1:3000/pair')
    
    @statusElement = $(element).find(".collaborate-status")
    @roomName = @statusElement.data('collaborate-room')
    
    @listen() 
    
    @socket.emit("watch_pair_room", {'room-name' : @roomName});
    
  
  listen: ->
    @socket.on 'status_updated', (data) =>
      if @roomName == data['room-name']
        @statusElement.text(data['status'])
