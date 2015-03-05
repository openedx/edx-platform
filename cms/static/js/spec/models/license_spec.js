define(["js/models/license"], function(LicenseModel) {
  describe("License model constructor", function() {
    it("accepts no arguments", function() {
      var model = new LicenseModel()
      expect(model.get("type")).toBeNull();
      expect(model.get("options")).toEqual({});
      expect(model.get("custom")).toBeFalsy();
    });

    it("accepts normal arguments", function() {
      var model = new LicenseModel({
        "type": "creative-commons",
        "options": {"fake-boolean": true, "version": "your momma"}
      });
      expect(model.get("type")).toEqual("creative-commons");
      expect(model.get("options")).toEqual({"fake-boolean": true, "version": "your momma"});
    })

    it("accepts a license string argument", function() {
      var model = new LicenseModel({"asString": "all-rights-reserved"});
      expect(model.get("type")).toEqual("all-rights-reserved");
      expect(model.get("options")).toEqual({});
      expect(model.get("custom")).toBeFalsy();
    });

    it("accepts a custom license argument", function() {
      var model = new LicenseModel({"asString": "Mozilla Public License 2.0"})
      expect(model.get("type")).toBeNull();
      expect(model.get("options")).toEqual({});
      expect(model.get("custom")).toEqual("Mozilla Public License 2.0");
    });
  });

  describe("License model", function() {
    beforeEach(function() {
      this.model = new LicenseModel();
    });

    it("can parse license strings", function() {
      this.model.setFromString("creative-commons: BY")
      expect(this.model.get("type")).toEqual("creative-commons")
      expect(this.model.get("options")).toEqual({"BY": true})
      expect(this.model.get("custom")).toBeFalsy();
    });

    it("can stringify a null license", function() {
      expect(this.model.toString()).toEqual("");
    });

    it("can stringify a simple license", function() {
      this.model.set("type", "foobie thinger");
      expect(this.model.toString()).toEqual("foobie thinger");
    });

    it("can stringify a license with options", function() {
      this.model.set({
        "type": "abc",
        "options": {"ping": "pong", "bing": true, "buzz": true, "beep": false}}
      );
      expect(this.model.toString()).toEqual("abc: ping=pong bing buzz");
    });

    it("can stringify a custom license", function() {
      this.model.set({
        "type": "doesn't matter",
        "options": {"ignore": "me"},
        "custom": "this is my super cool license"
      });
      expect(this.model.toString()).toEqual("this is my super cool license");
    });
  })
})
