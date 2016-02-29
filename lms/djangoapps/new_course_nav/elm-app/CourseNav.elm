module CourseNav (update, view) where

import Effects exposing (Effects)
import Html
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


-- view
view : Signal.Address Action -> CourseBlock -> Html.Html
view address courseBlock =
  case courseBlock of
    Empty ->
      Html.text "Loading..."

    Course attributes children ->
        Html.text attributes.displayName

    Error ->
      Html.text "Error - Some sort of HTTP error occurred"

    _ ->
      Html.text "Error - expected a course."
