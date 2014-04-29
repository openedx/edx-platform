Annotator.Plugin.Auth.prototype.haveValidToken = function() {
    return (
      this._unsafeToken &&
      this._unsafeToken.d.issuedAt &&
      this._unsafeToken.d.ttl &&
      this._unsafeToken.d.consumerKey &&
      this.timeToExpiry() > 0
    );
};

Annotator.Plugin.Auth.prototype.timeToExpiry = function() {
    var expiry, issue, now, timeToExpiry;
    now = new Date().getTime() / 1000;
    issue = createDateFromISO8601(this._unsafeToken.d.issuedAt).getTime() / 1000;
    expiry = issue + this._unsafeToken.d.ttl;
    timeToExpiry = expiry - now;
    if (timeToExpiry > 0) {
      return timeToExpiry;
    } else {
      return 0;
    }
};