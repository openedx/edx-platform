module CourseOutline (update, view) where

import Effects exposing (Effects)
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Task

import ParseCourse
import Styles
import Types exposing (..)
import CourseNav exposing (courseNavView)


update : CourseBlocksAction -> CourseBlock -> (CourseBlock, Effects CourseBlocksAction)
update action courseBlock =
    case action of
      -- Feed the API response result back as either 'CourseBlocksApiSuccess'
      -- or 'CourseBlocksApiError'.
      CourseBlocksApiResponse result ->
        case result of
          Ok blocksData ->
            ( courseBlock
            , blocksData
              |> Task.succeed
              |> Task.map CourseBlocksApiSuccess
              |> Effects.task
            )

          Err error ->
            ( courseBlock, Effects.task (Task.succeed (CourseBlocksApiError error)) )

      CourseBlocksApiSuccess blocksData ->
        ( ParseCourse.fromApiResponse blocksData, Effects.none )

      CourseBlocksApiError error ->
        ( Error, Effects.none )


view : Signal.Address CourseBlocksAction -> CourseBlock -> Html
view address courseBlock =
    case courseBlock of
      Empty ->
          div [ class "depth col-4 pre-4 post-4" ] [ text "Loading..." ]

      Course attributes children ->
        let
          -- TODO: Update this to represent the actual location in the course
          -- this can be done using the mobile api. See:
          -- http://edx.readthedocs.org/projects/edx-platform-api/en/latest/mobile/users.html#get-or-change-user-status-in-a-course
          currentLocation = "users > most recent > location"
        in
          div
            []
            [ courseNavView currentLocation ("search-" ++ attributes.id)
            , div
              [ class "depth" ]
              (List.map (chapterOutlineView address) children)
            ]

      Error ->
        div [] [ text "Error - Some sort of HTTP error occurred" ]

      _ ->
        div [] [ text "Error - expected a course." ]


chapterOutlineView : Signal.Address CourseBlocksAction -> CourseBlock -> Html
chapterOutlineView address courseBlock =
  case courseBlock of
    Chapter attributes children ->
      div
        [ Styles.chapterOutlineStyles ]
        [ h4
            [ class "hd-4"
            , id ("hd-" ++ attributes.id)
            ]
            [ text attributes.displayName ]
        , ul
            [ class "list-grouped"
            , attribute "aria-labelledby" ("hd-" ++ attributes.id)
            ]
            ( List.map (sequentialOutlineView address) children )
        ]

    _ ->
      div [] []


sequentialOutlineView : Signal.Address CourseBlocksAction -> CourseBlock -> Html
sequentialOutlineView address courseBlock =
  case courseBlock of
    Sequential attributes children ->
      li
        [ class "item has-block-link" ]
        [ a [ href <| "#block/" ++ attributes.id ] [ text attributes.displayName ] ]

    _ ->
      li [] []
