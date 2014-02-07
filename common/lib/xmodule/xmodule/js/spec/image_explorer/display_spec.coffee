describe 'ImageExplorer', ->
    beforeEach ->
        loadFixtures 'image_explorer.html'
    describe 'constructor', ->
        el = $('.xblock-student_view.xmodule_ImageExplorerModule')
        beforeEach ->
            @image_explorer = new ImageExplorer(el)
            @image_explorer.close_hotspots()

        it 'no hotspot should be visible on load', ->
            # disable test for now as we figure out the Jasmine/css relationship
            return
            visible_counter = 0
            $('.image-explorer-hotspot-reveal').each(
                (index, el)->
                    if $(el).css('display') == 'block'
                        visible_counter = visible_counter + 1
            )
            expect(visible_counter).toBe(0)

        it 'clicking on a hotspot will reveal an overlay and hide all others', ->
            # disable test for now as we figure out the Jasmine/css relationship
            return
            $('.image-explorer-hotspot').each(
                (index, el)->
                    el.click()
                    reveal = $(el).find('.image-explorer-hotspot-reveal')
                    expect(reveal.css('display')).toBe('block');

                    visible_counter = 0
                    $('.image-explorer-hotspot-reveal').each(
                        (index, el)->
                            if $(el).css('display') == 'block'
                                visible_counter = visible_counter + 1
                    )
                    expect(visible_counter).toBe(1)
            )
