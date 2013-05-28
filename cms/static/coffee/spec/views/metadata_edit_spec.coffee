beforeEach ->
    # TODO: update these
    setFixtures(sandbox({id: "page-alert"}))
    appendSetFixtures(sandbox({id: "page-notification"}))

describe "CMS.Views.Metadata.Editor creates editors for each field", ->
    beforeEach ->
        @model = new Backbone.Model({
        display_name: {
            default_value: null,
            display_name: "Display Name",
            explicitly_set: true,
            field_name: "display_name",
            help: "Specifies the name for this component. The name appears as a tooltip in the course ribbon at the top of the page.",
            inheritable: false,
            options: [],
            type: "Generic",
            value: "Word cloud"
            },
        num_inputs: {
            default_value: 5,
            display_name: "Inputs",
            explicitly_set: false,
            field_name: "num_inputs",
            help: "Number of text boxes for student to input words/sentences.",
            inheritable: false,
            options: {min: 1},
            type: "Integer",
            value: 5
            }
        })

    it "renders on initalize", ->
        view = new CMS.Views.Metadata.Editor({model: @model})
        expect(view.models).toBeDefined()
