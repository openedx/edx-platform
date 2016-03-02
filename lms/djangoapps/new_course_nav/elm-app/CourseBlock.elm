module CourseBlock (..) where


import Html exposing (..)
import Html.Attributes exposing (..)
import Types
import CourseNav exposing (courseNavView)


type alias BlockId =
  String

type alias Model =
  BlockId

type Action
  = NoOp


view : Signal.Address Action -> Model -> Html
view address model =
  if model == "" then
    text "Error loading block - no block URL"
  else
    div
      []
      [ courseNavView "Go Back!" ("search-" ++ model)
      , iframe
        [ src <| "/xblock/" ++ model
        , style
          [ ("width", "100%")
          , ("height", "1000px")
          ]
        ]
        []
      ]
