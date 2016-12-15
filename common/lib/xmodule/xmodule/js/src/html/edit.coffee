class @HTMLEditingDescriptor

  # custom fonts are prepended to font selection dropdown
  CUSTOM_FONTS = "Default='Open Sans', Verdana, Arial, Helvetica, sans-serif;"

  # list of standard tinyMCE fonts: http://www.tinymce.com/wiki.php/Configuration:font_formats
  STANDARD_FONTS = "Andale Mono=andale mono,times;"+
    "Arial=arial,helvetica,sans-serif;"+
    "Arial Black=arial black,avant garde;"+
    "Book Antiqua=book antiqua,palatino;"+
    "Comic Sans MS=comic sans ms,sans-serif;"+
    "Courier New=courier new,courier;"+
    "Georgia=georgia,palatino;"+
    "Helvetica=helvetica;"+
    "Impact=impact,chicago;"+
    "Symbol=symbol;"+
    "Tahoma=tahoma,arial,helvetica,sans-serif;"+
    "Terminal=terminal,monaco;"+
    "Times New Roman=times new roman,times;"+
    "Trebuchet MS=trebuchet ms,geneva;"+
    "Verdana=verdana,geneva;"+
    "Webdings=webdings;"+
    "Wingdings=wingdings,zapf dingbats"

  _getFonts = () ->
    CUSTOM_FONTS + STANDARD_FONTS

  constructor: (element) ->
    @element = element
    @base_asset_url = @element.find("#editor-tab").data('base-asset-url')
    @editor_choice = @element.find("#editor-tab").data('editor')
    if @base_asset_url == undefined
      @base_asset_url = null

    # We always create the "raw editor" so we can get the text out of it if necessary on save.
    @advanced_editor = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
        mode: "text/html"
        lineNumbers: true
        lineWrapping: true
    })

    if @editor_choice == 'visual'
      @$advancedEditorWrapper = $(@advanced_editor.getWrapperElement())
      @$advancedEditorWrapper.addClass('is-inactive')
      # Create an array of all content CSS links to use in and pass to Tiny MCE.
      # We create this dynamically in order to support hashed files from our Django pipeline.
      # CSS files that are to be used by Tiny MCE should contain the string "tinymce" so
      # they can be found by the search below.
      # We filter for only those files that are "content" files (as opposed to "skin" files).
      tiny_mce_css_links = []
      $("link[rel=stylesheet][href*='tinymce']").filter("[href*='content']").each ->
          tiny_mce_css_links.push $(this).attr("href")
          return

  #   This is a workaround for the fact that tinyMCE's baseURL property is not getting correctly set on AWS
  #   instances (like sandbox). It is not necessary to explicitly set baseURL when running locally.
      tinyMCE.baseURL = "#{baseUrl}/js/vendor/tinymce/js/tinymce"
  #   This is necessary for the LMS bulk e-mail acceptance test. In that particular scenario,
  #   tinyMCE incorrectly decides that the suffix should be "", which means it fails to load files.
      tinyMCE.suffix = ".min"
      @tiny_mce_textarea = $(".tiny-mce", @element).tinymce({
        script_url : "#{baseUrl}/js/vendor/tinymce/js/tinymce/tinymce.full.min.js",
        font_formats : _getFonts(),
        theme : "modern",
        skin: 'studio-tmce4',
        schema: "html5",
        # Necessary to preserve relative URLs to our images.
        convert_urls : false,
        # Sniff UI direction from `.wrapper-view` in studio or `.window-wrap` in LMS
        directionality: $(".wrapper-view, .window-wrap").prop('dir'),
        content_css : tiny_mce_css_links.join(", "),
        formats : {
          # tinyMCE does block level for code by default
          code: {inline: 'code'}
        },
        # Disable visual aid on borderless table.
        visual: false,
        target_list: [
          {title: 'New page', value: '_blank'},
          {title: 'None', value: '_self'},
        ]
        plugins: "textcolor, link, image, codemirror",
        codemirror: {
          path: "#{baseUrl}/js/vendor"
        },
        image_advtab: true,
        # We may want to add "styleselect" when we collect all styles used throughout the LMS
        toolbar: "formatselect | fontselect | bold italic underline forecolor wrapAsCode | bullist numlist outdent indent blockquote | link unlink image | code",
        block_formats: interpolate("%(paragraph)s=p;%(preformatted)s=pre;%(heading3)s=h3;%(heading4)s=h4;%(heading5)s=h5;%(heading6)s=h6", {
            paragraph: gettext("Paragraph"),
            preformatted: gettext("Preformatted"),
            heading3: gettext("Heading 3"),
            heading4: gettext("Heading 4"),
            heading5: gettext("Heading 5"),
            heading6: gettext("Heading 6")
          }, true),
        width: '100%',
        height: '400px',
        menubar: false,
        statusbar: false,

        # Necessary to avoid stripping of style tags.
        valid_children : "+body[style]",

        # Allow any elements to be used, e.g. link, script, math
        valid_elements: "*[*]",
        extended_valid_elements: "*[*]",
        invalid_elements: "",

        setup: @setupTinyMCE,
        # Cannot get access to tinyMCE Editor instance (for focusing) until after it is rendered.
        # The tinyMCE callback passes in the editor as a parameter.
        init_instance_callback: @initInstanceCallback,

        browser_spellcheck: true
      })
      tinymce.addI18n('en', {
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Add to Dictionary": gettext("Add to Dictionary"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Advanced": gettext("Advanced"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Align center": gettext("Align center"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Align left": gettext("Align left"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Align right": gettext("Align right"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Alignment": gettext("Alignment"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Alternative source": gettext("Alternative source"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Anchor": gettext("Anchor"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Anchors": gettext("Anchors"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Author": gettext("Author"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Background color": gettext("Background color"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Blockquote": gettext("Blockquote"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Blocks": gettext("Blocks"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Body": gettext("Body"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Bold": gettext("Bold"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Border color": gettext("Border color"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Border": gettext("Border"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Bottom": gettext("Bottom"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Bullet list": gettext("Bullet list"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cancel": gettext("Cancel"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Caption": gettext("Caption"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cell padding": gettext("Cell padding"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cell properties": gettext("Cell properties"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cell spacing": gettext("Cell spacing"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cell type": gettext("Cell type"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cell": gettext("Cell"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Center": gettext("Center"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Circle": gettext("Circle"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Clear formatting": gettext("Clear formatting"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Close": gettext("Close"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Code block": gettext("Code block"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Code": gettext("Code"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Color": gettext("Color"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cols": gettext("Cols"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Column group": gettext("Column group"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Column": gettext("Column"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Constrain proportions": gettext("Constrain proportions"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Copy row": gettext("Copy row"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Copy": gettext("Copy"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Could not find the specified string.": gettext("Could not find the specified string."),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Custom color": gettext("Custom color"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Custom...": gettext("Custom..."),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cut row": gettext("Cut row"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Cut": gettext("Cut"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Decrease indent": gettext("Decrease indent"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Default": gettext("Default"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Delete column": gettext("Delete column"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Delete row": gettext("Delete row"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Delete table": gettext("Delete table"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Description": gettext("Description"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Dimensions": gettext("Dimensions"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Disc": gettext("Disc"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Div": gettext("Div"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Document properties": gettext("Document properties"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Edit HTML": gettext("Edit HTML"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Edit": gettext("Edit"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Embed": gettext("Embed"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Emoticons": gettext("Emoticons"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Encoding": gettext("Encoding"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "File": gettext("File"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Find and replace": gettext("Find and replace"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Find next": gettext("Find next"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Find previous": gettext("Find previous"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Find": gettext("Find"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Finish": gettext("Finish"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Font Family": gettext("Font Family"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Font Sizes": gettext("Font Sizes"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Footer": gettext("Footer"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Format": gettext("Format"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Formats": gettext("Formats"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Fullscreen": gettext("Fullscreen"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "General": gettext("General"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "H Align": gettext("H Align"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header 1": gettext("Header 1"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header 2": gettext("Header 2"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header 3": gettext("Header 3"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header 4": gettext("Header 4"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header 5": gettext("Header 5"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header 6": gettext("Header 6"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header cell": gettext("Header cell"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Header": gettext("Header"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Headers": gettext("Headers"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Heading 1": gettext("Heading 1"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Heading 2": gettext("Heading 2"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Heading 3": gettext("Heading 3"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Heading 4": gettext("Heading 4"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Heading 5": gettext("Heading 5"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Heading 6": gettext("Heading 6"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Headings": gettext("Headings"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Height": gettext("Height"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Horizontal line": gettext("Horizontal line"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Horizontal space": gettext("Horizontal space"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "HTML source code": gettext("HTML source code"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Ignore all": gettext("Ignore all"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Ignore": gettext("Ignore"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Image description": gettext("Image description"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Increase indent": gettext("Increase indent"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Inline": gettext("Inline"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert column after": gettext("Insert column after"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert column before": gettext("Insert column before"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert date/time": gettext("Insert date/time"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert image": gettext("Insert image"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert link": gettext("Insert link"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert row after": gettext("Insert row after"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert row before": gettext("Insert row before"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert table": gettext("Insert table"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert template": gettext("Insert template"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert video": gettext("Insert video"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert": gettext("Insert"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert/edit image": gettext("Insert/edit image"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert/edit link": gettext("Insert/edit link"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Insert/edit video": gettext("Insert/edit video"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Italic": gettext("Italic"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Justify": gettext("Justify"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Keywords": gettext("Keywords"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Left to right": gettext("Left to right"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Left": gettext("Left"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Lower Alpha": gettext("Lower Alpha"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Lower Greek": gettext("Lower Greek"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Lower Roman": gettext("Lower Roman"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Match case": gettext("Match case"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Merge cells": gettext("Merge cells"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Middle": gettext("Middle"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Name": gettext("Name"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "New document": gettext("New document"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "New window": gettext("New window"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Next": gettext("Next"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "No color": gettext("No color"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Nonbreaking space": gettext("Nonbreaking space"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "None": gettext("None"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Numbered list": gettext("Numbered list"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Ok": gettext("Ok"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "OK": gettext("OK"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Page break": gettext("Page break"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paragraph": gettext("Paragraph"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paste as text": gettext("Paste as text"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paste is now in plain text mode. Contents will now be pasted as plain text until you toggle this option off.": gettext("Paste is now in plain text mode. Contents will now be pasted as plain text until you toggle this option off."),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paste row after": gettext("Paste row after"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paste row before": gettext("Paste row before"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paste your embed code below:": gettext("Paste your embed code below:"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Paste": gettext("Paste"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Poster": gettext("Poster"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Pre": gettext("Pre"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Prev": gettext("Prev"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Preview": gettext("Preview"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Print": gettext("Print"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Redo": gettext("Redo"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Remove link": gettext("Remove link"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Replace all": gettext("Replace all"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Replace all": gettext("Replace all"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Replace with": gettext("Replace with"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Replace": gettext("Replace"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Replace": gettext("Replace"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Restore last draft": gettext("Restore last draft"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help": gettext("Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Right to left": gettext("Right to left"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Right": gettext("Right"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Robots": gettext("Robots"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Row group": gettext("Row group"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Row properties": gettext("Row properties"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Row type": gettext("Row type"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Row": gettext("Row"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Rows": gettext("Rows"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Save": gettext("Save"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Scope": gettext("Scope"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Select all": gettext("Select all"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Show blocks": gettext("Show blocks"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Show invisible characters": gettext("Show invisible characters"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Source code": gettext("Source code"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Source": gettext("Source"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Special character": gettext("Special character"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Spellcheck": gettext("Spellcheck"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Split cell": gettext("Split cell"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Square": gettext("Square"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Start search": gettext("Start search"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Strikethrough": gettext("Strikethrough"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Style": gettext("Style"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Subscript": gettext("Subscript"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Superscript": gettext("Superscript"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Table properties": gettext("Table properties"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Table": gettext("Table"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Target": gettext("Target"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Templates": gettext("Templates"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Text color": gettext("Text color"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Text to display": gettext("Text to display"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "The URL you entered seems to be an email address. Do you want to add the required mailto: prefix?": gettext("The URL you entered seems to be an email address. Do you want to add the required mailto: prefix?"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "The URL you entered seems to be an external link. Do you want to add the required http:// prefix?": gettext("The URL you entered seems to be an external link. Do you want to add the required http:// prefix?"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Title": gettext("Title"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Tools": gettext("Tools"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Top": gettext("Top"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Underline": gettext("Underline"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Undo": gettext("Undo"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Upper Alpha": gettext("Upper Alpha"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Upper Roman": gettext("Upper Roman"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Url": gettext("Url"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "V Align": gettext("V Align"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Vertical space": gettext("Vertical space"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "View": gettext("View"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Visual aids": gettext("Visual aids"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Whole words": gettext("Whole words"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Width": gettext("Width"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Words: {0}": gettext("Words: {0}"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "You have unsaved changes are you sure you want to navigate away?": gettext("You have unsaved changes are you sure you want to navigate away?"),
        ###
        Translators: this is a message from the raw HTML editor displayed in the browser when a user needs to edit HTML
        ###
        "Your browser doesn't support direct access to the clipboard. Please use the Ctrl+X/C/V keyboard shortcuts instead.": gettext("Your browser doesn't support direct access to the clipboard. Please use the Ctrl+X/C/V keyboard shortcuts instead."),
      })

  setupTinyMCE: (ed) =>
    ed.addButton('wrapAsCode', {
      title : 'Code block',
      image : "#{baseUrl}/images/ico-tinymce-code.png",
      onclick : () ->
        ed.formatter.toggle('code')
    })

    @visualEditor = ed

    # These events were added to the plugin code as the TinyMCE PluginManager
    # does not fire any events when plugins are opened or closed.
    ed.on('SaveImage', @saveImage)
    ed.on('EditImage', @editImage)
    ed.on('SaveLink', @saveLink)
    ed.on('EditLink', @editLink)
    ed.on('ShowCodeEditor', @showCodeEditor)
    ed.on('SaveCodeEditor', @saveCodeEditor)

  editImage: (data) =>
    # Called when the image plugin will be shown. Input arg is the JSON version of the image data.
    if data['src']
      data['src'] = rewriteStaticLinks(data['src'], @base_asset_url, '/static/')

  saveImage: (data) =>
    # Called when the image plugin is saved. Input arg is the JSON version of the image data.
    if data['src']
      data['src'] = rewriteStaticLinks(data['src'], '/static/', @base_asset_url)

  editLink: (data) =>
    # Called when the link plugin will be shown. Input arg is the JSON version of the link data.
    if data['href']
      data['href'] = rewriteStaticLinks(data['href'], @base_asset_url, '/static/')

  saveLink: (data) =>
    # Called when the link plugin is saved. Input arg is the JSON version of the link data.
    if data['href']
      data['href'] = rewriteStaticLinks(data['href'], '/static/', @base_asset_url)

  showCodeEditor: (source) =>
    # Called when the CodeMirror Editor is displayed to convert links to show static prefix.
    # The input argument is a dict with the text content.
    content = rewriteStaticLinks(source.content, @base_asset_url, '/static/')
    source.content = content

  saveCodeEditor: (source) =>
    # Called when the CodeMirror Editor is saved to convert links back to the full form.
    # The input argument is a dict with the text content.
    content = rewriteStaticLinks(source.content, '/static/', @base_asset_url)
    source.content = content

  initInstanceCallback: (visualEditor) =>
    visualEditor.setContent(rewriteStaticLinks(visualEditor.getContent({no_events: 1}), '/static/', @base_asset_url))
    # Unfortunately, just setting visualEditor.isNortDirty = true is not enough to convince TinyMCE we
    # haven't dirtied the Editor. Store the raw content so we can compare it later.
    @starting_content = visualEditor.getContent({format:"raw", no_events: 1})
    visualEditor.focus()

  getVisualEditor: () ->
    ###
    Returns the instance of TinyMCE.

    Pulled out as a helper method for unit test.
    ###
    return @visualEditor

  _validateString = (string) ->
    regexp = /%%[^%\s]+%%/g
    keywordsSupported = [
      '%%USERNAME%%',
      '%%USER_ID%%',
      '%%USER_FULLNAME%%',
      '%%COURSE_DISPLAY_NAME%%',
      '%%COURSE_ID%%',
      '%%COURSE_START_DATE%%',
      '%%COURSE_END_DATE%%',
    ]

    keywordsFound = string.match(regexp) || []
    keywordsInvalid = $.map(keywordsFound, (keyword) ->
      if $.inArray(keyword, keywordsSupported) == -1
        keyword
      else
        null
    )

    'isValid': keywordsInvalid.length == 0
    'keywordsInvalid': keywordsInvalid

  save: ->
    text = undefined
    if @editor_choice == 'visual'
      visualEditor = @getVisualEditor()
      raw_content = visualEditor.getContent({format:"raw", no_events: 1})
      if @starting_content != raw_content
        text = rewriteStaticLinks(visualEditor.getContent({no_events: 1}), @base_asset_url, '/static/')

    if text == undefined
      text = @advanced_editor.getValue()

    validation = _validateString(text)
    if not validation.isValid
      message = gettext('There are invalid keywords in your email. Please check the following keywords and try again:')
      message += '\n' + validation.keywordsInvalid.join('\n')
      alert(message)
      return null

    data: text
