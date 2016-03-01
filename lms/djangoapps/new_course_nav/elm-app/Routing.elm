module Routing (..) where

import Effects exposing (Effects)
import Hop


type Action
  = HopAction Hop.Action
  | ShowCourseOutline Hop.Payload
  | ShowBlock Hop.Payload
  | ShowNotFound Hop.Payload


type alias Model =
  { routerPayload : Hop.Payload
  , currentView : String
  }


initialModel : Model
initialModel =
  { routerPayload = router.payload
  , currentView = "courseOutline"
  }


update : Action -> Model -> (Model, Effects a)
update action model =
  case action of
    ShowCourseOutline payload ->
      ( { model | currentView = "courseOutline", routerPayload = payload }
      , Effects.none
      )

    ShowBlock payload ->
      ( { model | currentView = "block", routerPayload = payload }
      , Effects.none
      )

    _ ->
      ( model, Effects.none )


routes : List (String, Hop.Payload -> Action)
routes =
  [ ("", ShowCourseOutline)
  , ("/block/:blockId", ShowBlock)
  ]


router : Hop.Router Action
router =
  Hop.new
    { routes = routes
    , notFoundAction = ShowNotFound
    }
