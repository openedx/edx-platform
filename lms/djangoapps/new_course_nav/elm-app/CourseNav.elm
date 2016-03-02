module CourseNav (..) where

import Html exposing (..)
import Html.Attributes exposing (..)
import Styles


type alias SearchId =
  String


type alias BreadcrumbsString =
  String


courseSearchView : SearchId -> Html
courseSearchView searchId =
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


breadcrumbsView : BreadcrumbsString -> Html
breadcrumbsView currentLocation =
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
      , text currentLocation
      ]
    ]


courseNavView : BreadcrumbsString -> SearchId -> Html
courseNavView breadcrumbsString searchId =
  div
    [ class "row" ]
    [ breadcrumbsView breadcrumbsString
    , courseSearchView searchId
    ]
