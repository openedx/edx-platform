module Main (..) where

import Html
import Html.Events
import StartApp.Simple


-- model
type alias Model =
  { count : Int }


initialModel =
  { count = 0 }

-- update
type Action
  = Increment
  | Decrement


update : Action -> Model -> Model
update action model =
  case action of
    Increment ->
      { model | count = model.count + 1 }

    Decrement ->
      { model | count = model.count - 1 }


-- view
view : Signal.Address Action -> Model -> Html.Html
view address model =
  Html.div
    []
    [ Html.div [] [ Html.text courseApiUrl ]
    , Html.div [] [ Html.text courseBlocksApiUrl ]
    , Html.div
        []
        [ Html.button
            [ Html.Events.onClick address Decrement ]
            [ Html.text "-" ]
        , Html.text ("Count: " ++ (toString model.count))
        , Html.button
            [ Html.Events.onClick address Increment ]
            [ Html.text "+" ]
        ]
    ]


main =
  StartApp.Simple.start
    { model = initialModel
    , update = update
    , view = view
    }


-- ports
port courseApiUrl : String


port courseBlocksApiUrl : String
