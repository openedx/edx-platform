describe "CMS.Models.FileUpload", ->
    beforeEach ->
        @model = new CMS.Models.FileUpload()

    it "is unfinished by default", ->
        expect(@model.get("finished")).toBeFalsy()

    it "is not uploading by default", ->
        expect(@model.get("uploading")).toBeFalsy()

    it "is valid by default", ->
        expect(@model.isValid()).toBeTruthy()

    it "is valid for PDF files by default", ->
        file = {"type": "application/pdf"}
        @model.set("selectedFile", file);
        expect(@model.isValid()).toBeTruthy()

    it "is invalid for text files by default", ->
        file = {"type": "text/plain"}
        @model.set("selectedFile", file);
        expect(@model.isValid()).toBeFalsy()

    it "is invalid for PNG files by default", ->
        file = {"type": "image/png"}
        @model.set("selectedFile", file);
        expect(@model.isValid()).toBeFalsy()

    it "can accept non-PDF files when explicitly set", ->
        file = {"type": "image/png"}
        @model.set("mimeTypes": ["image/png"])
        @model.set("selectedFile", file)
        expect(@model.isValid()).toBeTruthy()
