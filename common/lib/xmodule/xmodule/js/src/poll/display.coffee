class @PollModule
  constructor: (element) ->
    @el = element
    @ajaxUrl = @$('.container').data('url')
    @$('.upvote').on('click', () => $.postWithPrefix(@url('upvote'), @handleVote))
    @$('.downvote').on('click', () => $.postWithPrefix(@url('downvote'), @handleVote))

  $: (selector) -> $(selector, @el)

  url: (target) -> "#{@ajaxUrl}/#{target}"

  handleVote: (response) =>
    @$('.container').replaceWith(response.results)