module CourseOutline (update, view) where

import Effects exposing (Effects)
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Task

import ParseCourse
import Styles
import Types exposing (..)


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


wrapWithContainer : List Html -> Html
wrapWithContainer htmlList =
  div
    [ class "grid-container grid-manual"
    , Styles.gridContainerStyle
    ]
    htmlList


courseSearchView : Signal.Address CourseBlocksAction -> CourseBlock -> Html
courseSearchView address courseBlock =
  case courseBlock of
    Course attributes children ->
      let
        searchId =
          ("search-" ++ attributes.id)
      in
        div
          [ class "col col-5" ]
          [ Html.form
            [ class "form" ]
            [ fieldset
              [ class "form-group" ]
              [ legend [ class "form-group-hd sr-only" ] [ text "Search Course" ]
              , div
                [ class "field" ]
                [ label
                  [ class "field-label sr-only", for searchId ]
                  [ text "Search this course" ]
                , input
                  [ class "field-input input-text"
                  , attribute "type" "search"
                  , id searchId
                  , name searchId
                  , placeholder "Search this course"
                  ]
                  [ text "" ]
                , button
                  [ class "btn-brand btn-small"
                  , attribute "type" "button"
                  , Styles.btnBrandStyle
                  ]
                  [ text "Search" ]
                ]
              ]
            ]
          ]
    _ ->
      div [] []

breadcrumbsView : Signal.Address CourseBlocksAction -> CourseBlock -> Html
breadcrumbsView address courseBlock =
  div
    [class "col col-7"]
    [ h3
      [ class "hd-4"
      ]
      [
        span
        [ class "icon-fallback icon-fallback-text"
        , style [ ("padding-right", "20px") ]
        ]
        [ span
            [ class "icon fa fa-bars", attribute "aria-hidden" "true" ]
            [ span
              [ class "text" ]
              [ text "Menu" ]
            ]
        ]
      , text "Week 1 > subsection 1"
      ]
    ]

view : Signal.Address CourseBlocksAction -> CourseBlock -> Html
view address courseBlock =
  case courseBlock of
    Empty ->
      wrapWithContainer
        [ div [ class "depth col-4 pre-4 post-4" ] [ text "Loading..." ] ]

    Course attributes children ->
        wrapWithContainer
          [ div
            [ class "row" ]
            [ breadcrumbsView address courseBlock
            , courseSearchView address courseBlock
            ]
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
        [ a [ href attributes.studentViewUrl ] [ text attributes.displayName ] ]

    _ ->
      li [] []
