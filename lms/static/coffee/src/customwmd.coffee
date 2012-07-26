$ ->
  converter = Markdown.getSanitizingConverter()
  editor = new Markdown.Editor(converter)
  converter.hooks.chain "preConversion", removeMath
  editor.run()
