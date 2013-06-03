describe "CMS.Models.Metadata", ->
    it "knows when the value has not been modified", ->
        model = new CMS.Models.Metadata(
            {'value': 'original', 'explicitly_set': false})
        expect(model.isModified()).toBeFalsy()

        model = new CMS.Models.Metadata(
            {'value': 'original', 'explicitly_set': true})
        model.setValue('original')
        expect(model.isModified()).toBeFalsy()

    it "knows when the value has been modified", ->
        model = new CMS.Models.Metadata(
            {'value': 'original', 'explicitly_set': false})
        model.setValue('original')
        expect(model.isModified()).toBeTruthy()

        model = new CMS.Models.Metadata(
            {'value': 'original', 'explicitly_set': true})
        model.setValue('modified')
        expect(model.isModified()).toBeTruthy()

    it "tracks when values have been explicitly set", ->
        model = new CMS.Models.Metadata(
            {'value': 'original', 'explicitly_set': false})
        expect(model.isExplicitlySet()).toBeFalsy()
        model.setValue('original')
        expect(model.isExplicitlySet()).toBeTruthy()

    it "has both 'display value' and a 'value' methods", ->
        model = new CMS.Models.Metadata(
            {'value': 'default', 'explicitly_set': false})
        expect(model.getValue()).toBeNull
        expect(model.getDisplayValue()).toBe('default')
        model.setValue('modified')
        expect(model.getValue()).toBe('modified')
        expect(model.getDisplayValue()).toBe('modified')

    it "has a clear method for reverting to the default", ->
        model = new CMS.Models.Metadata(
            {'value': 'original', 'default_value' : 'default', 'explicitly_set': true})
        model.clear()
        expect(model.getValue()).toBeNull
        expect(model.getDisplayValue()).toBe('default')
        expect(model.isExplicitlySet()).toBeFalsy()

    it "has a getter for field name", ->
        model = new CMS.Models.Metadata({'field_name': 'foo'})
        expect(model.getFieldName()).toBe('foo')

    it "has a getter for options", ->
        model = new CMS.Models.Metadata({'options': ['foo', 'bar']})
        expect(model.getOptions()).toEqual(['foo', 'bar'])

    it "has a getter for type", ->
        model = new CMS.Models.Metadata({'type': 'Integer'})
        expect(model.getType()).toBe(CMS.Models.Metadata.INTEGER_TYPE)

