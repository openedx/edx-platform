const getCookies = () => {
  return document.cookie.split(';').reduce((memo, str) => {
    const split = str.trim().split('=');
    memo[split[0]] = split[1];
    return memo;
  }, {});
};

const getCsrf = () => {
  const cookies = getCookies();
  return cookies.csrftoken;
};

export const get = (url) => {
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
};

export const patch = (url, data) => {
  console.log(data);
  return fetch(url, {
    method: 'PATCH',
    credentials: 'same-origin',
    'headers': {
      'Content-Type': 'application/merge-patch+json',
      'X-CSRFToken': getCsrf()
    },
    body: JSON.stringify(data)
  })
  .then(data => data.json())
  .catch(error => {
    throw error;
  });
};
