import Cookies from "js-cookie";

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

export const getSettings = async ({ runtime, xblockElement }) => (
  fetch(
    runtime.handlerUrl(xblockElement, 'load_settings'),
    {credentials: 'same-origin', method: 'get', headers: HEADERS},
  ).then((response) => response.json())
)

export const postSettings = async ({ runtime, xblockElement, changes }) => (
  fetch(
    runtime.handlerUrl(xblockElement, 'save_settings'),
    {credentials: 'same-origin', method: 'post', headers: HEADERS, body: JSON.stringify(changes)},
  ).then(
    async (response) => {
      if ((response.status >= 300) || (response.status < 200)) {
        const err = Error('API error.')
        err.data = (
          (await response.json()) || {'detail': gettext('We had trouble saving this block. Please try again later.')}
        )
        throw err
      }
      return await response.json()
    },
  )
)
