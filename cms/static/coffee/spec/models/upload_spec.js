define ["js/models/uploads"], (FileUpload) ->

    describe "FileUpload", ->
        beforeEach ->
            @model = new FileUpload()

        it "is unfinished by default", ->
            expect(@model.get("finished")).toBeFalsy()

        it "is not uploading by default", ->
            expect(@model.get("uploading")).toBeFalsy()

        it "is valid by default", ->
            expect(@model.isValid()).toBeTruthy()

        it "is valid for text files by default", ->
            file = {"type": "text/plain", "name": "filename.txt"}
            @model.set("selectedFile", file);
            expect(@model.isValid()).toBeTruthy()

        it "is valid for PNG files by default", ->
            file = {"type": "image/png", "name": "filename.png"}
            @model.set("selectedFile", file);
            expect(@model.isValid()).toBeTruthy()

        it "can accept a file type when explicitly set", ->
            file = {"type": "image/png", "name": "filename.png"}
            @model.set("mimeTypes": ["image/png"])
            @model.set("selectedFile", file)
            expect(@model.isValid()).toBeTruthy()

        it "can accept a file format when explicitly set", ->
            file = {"type": "", "name": "filename.png"}
            @model.set("fileFormats": ["png"])
            @model.set("selectedFile", file)
            expect(@model.isValid()).toBeTruthy()

        it "can accept multiple file types", ->
            file = {"type": "image/gif", "name": "filename.gif"}
            @model.set("mimeTypes": ["image/png", "image/jpeg", "image/gif"])
            @model.set("selectedFile", file)
            expect(@model.isValid()).toBeTruthy()

        it "can accept multiple file formats", ->
            file = {"type": "image/gif", "name": "filename.gif"}
            @model.set("fileFormats": ["png", "jpeg", "gif"])
            @model.set("selectedFile", file)
            expect(@model.isValid()).toBeTruthy()

        describe "fileTypes", ->
          it "returns a list of the uploader's file types", ->
            @model.set('mimeTypes', ['image/png', 'application/json'])
            @model.set('fileFormats', ['gif', 'srt'])
            expect(@model.fileTypes()).toEqual(['PNG', 'JSON', 'GIF', 'SRT'])

        describe "formatValidTypes", ->
          it "returns a map of formatted file types and extensions", ->
            @model.set('mimeTypes', ['image/png', 'image/jpeg', 'application/json'])
            formatted = @model.formatValidTypes()
            expect(formatted).toEqual(
              fileTypes: 'PNG, JPEG or JSON',
              fileExtensions: '.png, .jpeg or .json'
            )

          it "does not format with only one mime type", ->
            @model.set('mimeTypes', ['application/pdf'])
            formatted = @model.formatValidTypes()
            expect(formatted).toEqual(
              fileTypes: 'PDF',
              fileExtensions: '.pdf'
            )
