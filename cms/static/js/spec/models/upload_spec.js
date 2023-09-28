define(["js/models/uploads"], FileUpload =>

    describe("FileUpload", function() {
        beforeEach(function() {
            this.model = new FileUpload();
        });

        it("is unfinished by default", function() {
            expect(this.model.get("finished")).toBeFalsy();
        });

        it("is not uploading by default", function() {
            expect(this.model.get("uploading")).toBeFalsy();
        });

        it("is valid by default", function() {
            expect(this.model.isValid()).toBeTruthy();
        });

        it("is valid for text files by default", function() {
            const file = {"type": "text/plain", "name": "filename.txt"};
            this.model.set("selectedFile", file);
            expect(this.model.isValid()).toBeTruthy();
        });

        it("is valid for PNG files by default", function() {
            const file = {"type": "image/png", "name": "filename.png"};
            this.model.set("selectedFile", file);
            expect(this.model.isValid()).toBeTruthy();
        });

        it("can accept a file type when explicitly set", function() {
            const file = {"type": "image/png", "name": "filename.png"};
            this.model.set({"mimeTypes": ["image/png"]});
            this.model.set("selectedFile", file);
            expect(this.model.isValid()).toBeTruthy();
        });

        it("can accept a file format when explicitly set", function() {
            const file = {"type": "", "name": "filename.png"};
            this.model.set({"fileFormats": ["png"]});
            this.model.set("selectedFile", file);
            expect(this.model.isValid()).toBeTruthy();
        });

        it("can accept multiple file types", function() {
            const file = {"type": "image/gif", "name": "filename.gif"};
            this.model.set({"mimeTypes": ["image/png", "image/jpeg", "image/gif"]});
            this.model.set("selectedFile", file);
            expect(this.model.isValid()).toBeTruthy();
        });

        it("can accept multiple file formats", function() {
            const file = {"type": "image/gif", "name": "filename.gif"};
            this.model.set({"fileFormats": ["png", "jpeg", "gif"]});
            this.model.set("selectedFile", file);
            expect(this.model.isValid()).toBeTruthy();
        });

        describe("fileTypes", () =>
          it("returns a list of the uploader's file types", function() {
            this.model.set('mimeTypes', ['image/png', 'application/json']);
            this.model.set('fileFormats', ['gif', 'srt']);
            expect(this.model.fileTypes()).toEqual(['PNG', 'JSON', 'GIF', 'SRT']);
          })
        );

        describe("formatValidTypes", function() {
          it("returns a map of formatted file types and extensions", function() {
            this.model.set('mimeTypes', ['image/png', 'image/jpeg', 'application/json']);
            const formatted = this.model.formatValidTypes();
            expect(formatted).toEqual({
              fileTypes: 'PNG, JPEG or JSON',
              fileExtensions: '.png, .jpeg or .json'
            });
          });

          it("does not format with only one mime type", function() {
            this.model.set('mimeTypes', ['application/pdf']);
            const formatted = this.model.formatValidTypes();
            expect(formatted).toEqual({
              fileTypes: 'PDF',
              fileExtensions: '.pdf'
            });
          });
        });
    })
);
