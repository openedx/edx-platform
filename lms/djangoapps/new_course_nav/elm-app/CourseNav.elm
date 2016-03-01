module CourseNav (update, courseOutlineView) where

import Effects exposing (Effects)
import Html exposing (..)
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


-- views

courseOutlineView : Signal.Address Action -> CourseBlock -> Html
courseOutlineView address courseBlock =
  case courseBlock of
    Empty ->
      div [] [ text "Loading..." ]

    Course attributes children ->
        div
          []
          ( div [] [text attributes.displayName ]
            :: List.map (chapterOutlineView address) children
          )

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
        ( div [] [ text attributes.displayName ]
          :: List.map (sequentialOutlineView address) children
        )

    -- We're expecting a chapter, so don't render anything else.
    _ ->
      div [] []


sequentialOutlineView : Signal.Address Action -> CourseBlock -> Html
sequentialOutlineView address courseBlock =
  case courseBlock of
    Sequential attributes children ->
      div
        []
        [ text attributes.displayName ]

    _ ->
      div [] []
