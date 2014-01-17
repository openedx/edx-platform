describe 'StudentNotes', ->

  beforeEach ->
    @studentNotes = new StudentNotes
    @localContext = {"window":{location:{href:"http://www.fake.com/result"}}}
  
  describe 'set up json', ->
    @expected = {"prefix":@getPrefix(), "loadFromSearch":{'uri':"test", "limit":0}, "annotationData":{'uri':"test"}}
    it 'set up json for store', ->
      expect(@getStoreConfig("test")).toEqual(@expected)
  
  describe 'dealing with urls', ->
    it 'getting prefix', ->
      expect(true).toBe(true)
    it 'getting uri path', ->
      expect(@getURIPath()).toEqual('/result')