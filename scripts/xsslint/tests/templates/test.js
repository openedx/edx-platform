var message = 'Rock & Roll';
var x = '<string>' + message + '</strong>';
var template = '<%= invalid %>';
// quiet the linter
// eslint-disable-next-line no-alert
alert(x);
// eslint-disable-next-line no-alert
alert(template);
