class @Time
  @format: (time) ->
    pad = (number) -> if number < 10 then  "0#{number}" else number

    seconds = Math.floor time
    minutes = Math.floor seconds / 60
    hours = Math.floor minutes / 60
    seconds = seconds % 60
    minutes = minutes % 60

    if hours
      "#{hours}:#{pad(minutes)}:#{pad(seconds % 60)}"
    else
      "#{minutes}:#{pad(seconds % 60)}"

  @convert: (time, oldSpeed, newSpeed) ->
    (time * oldSpeed / newSpeed).toFixed(3)
