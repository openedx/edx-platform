export const get = (url, success, error) => {
  return fetch(url, {
    credentials: 'same-origin',
    headers: {
      'Accept': 'application/json',
    }
  })
  .then((data) => data.json())
  .catch((error) => {
    throw error;
  });
  // .then((json) => {
  //   success(json);
  // });
}
