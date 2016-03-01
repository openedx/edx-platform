module CourseNav (update, courseOutlineView) where

import Effects exposing (Effects)
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Task

import ParseCourse
import NavTypes exposing (..)


update : Action -> CourseBlock -> (CourseBlock, Effects Action)
update action courseBlock =
  -- TODO: can we flatten the Ok/Err results into action types?
  let
    foo = Debug.log (toString action)
  in
    case action of
      CourseBlocksApiResponse result ->
        case result of
          Ok value ->
            -- TODO: handle failure value
            ( ParseCourse.fromApiResponse value, Effects.none )

          Err value ->
            ( courseBlock, Effects.task (Task.succeed (CourseBlocksApiError value)) )

      CourseBlocksApiError value ->
        ( Error, Effects.none )


wrapWithContainer : List Html -> Html
wrapWithContainer htmlList =
  div
    [ class "grid-container" ]
    htmlList


courseOutlineView : Signal.Address Action -> CourseBlock -> Html
courseOutlineView address courseBlock =
  case courseBlock of
    Empty ->
      wrapWithContainer
        [ div [ class "depth col-4 pre-4 post-4" ] [ text "Loading..." ] ]

    Course attributes children ->
      wrapWithContainer
        [ div
          [ class "depth" ]
          [ h3 [ class "hd-3 emphasized" ] [text attributes.displayName ] ]
        , div
          [ class "depth" ]
          (List.map (chapterOutlineView address) children)
        ]

    Error ->
      div [] [ text "Error - Some sort of HTTP error occurred" ]

    _ ->
      div [] [ text "Error - expected a course." ]


chapterOutlineView : Signal.Address Action -> CourseBlock -> Html
chapterOutlineView address courseBlock =
  case courseBlock of
    Chapter attributes children ->
      div
        []
        ( h4 [ class "hd-4" ] [ text attributes.displayName ]
          :: List.map (sequentialOutlineView address) children
        )

    _ ->
      div [] []


sequentialOutlineView : Signal.Address Action -> CourseBlock -> Html
sequentialOutlineView address courseBlock =
  case courseBlock of
    Sequential attributes children ->
      div
        [ class "card" ]
        [ h5
            [ class "hd-5" ]
            [ a [ href attributes.lmsWebUrl ] [ text attributes.displayName ] ]
        ]

    _ ->
      div [] []
