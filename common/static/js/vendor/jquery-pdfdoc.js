/**
 * jQuery PDF-DOC Plugin
 *
 * LICENSE
 *
 * This source file is subject to the Apache Licence, Version 2.0 that is bundled
 * with this package in the file LICENSE.txt.
 * It is also available through the world-wide-web at this URL:
 * http://dev.funkynerd.com/projects/hazaar/wiki/licence
 * If you did not receive a copy of the license and are unable to
 * obtain it through the world-wide-web, please send an email
 * to license@funkynerd.com so we can send you a copy immediately.
 *
 * @copyright   Copyright (c) 2012 Jamie Carl (http://www.funkynerd.com)
 * @license     http://dev.funkynerd.com/projects/hazaar/wiki/licence Apache Licence, Version 2.0
 * @version     0.7
 */

//PDFJS.workerSrc = 'hazaar/js/pdf.js';

PDFJS.disableWorker = true;

(function ( $ ){
    $.fn.PDFDoc = function( options ) {

        renderPage = function (pdf, the_page, canvas, scale){
            
              // Using promise to fetch the page
              pdf.getPage(the_page).then(function(page) {
                
                var viewport = page.getViewport(scale);
            
                var context = canvas.getContext('2d');
                
                canvas.height = viewport.height;
                
                canvas.width = viewport.width;
            
                page.render( { canvasContext: context, viewport: viewport } );
                
                $('#h-page-input').val(the_page);
                
              });
              
        }

        var settings = $.extend( {
              'page'                : 1,
              'scale'               : 1
        }, options);
        
        if(!settings.source){
        
            $.error('No PDF document source was given');
            
            return this;
                
        }
        
        var mydoc = this;
        
        var page_count = 0;
        
        mydoc.addClass('h-pdf-container');
        
        var canvas_container = $('<div>', { 'class' : 'h-pdf-canvas-container' } );
        
        var canvas = $('<canvas>', { 'class' : 'h-pdf-canvas'});
        
        canvas.dblclick(function(event){
            
            var scale = mydoc.data('scale');
            
            scale += 0.5;
            
            mydoc.data('scale', scale);
            
            renderPage(mydoc.data('pdf'), mydoc.data('current_page'), $(this).get()[0], scale);
            
            $('#page-zoom').val(scale);

        });
        
        
        /*
         *Create the toolbar layouts
         */
        var toolbar = $('<div>', { 'class' : 'h-pdf-toolbar'});   
        
        var toolbar_left = $('<div>', { 'class' : 'h-pdf-toolbar-left' } );
        
        var toolbar_right = $('<div>', { 'class' : 'h-pdf-toolbar-right' } );
        
        var toolbar_center = $('<div>').addClass('h-pdf-toolbar-center');
        
        toolbar.append(toolbar_left).append(toolbar_right).append(toolbar_center);
        
        mydoc.append(toolbar);
        
        /*
         * Create the nav buttons
         */
        var but_next = $('<div>', { 'class' : 'h-pdf-button h-pdf-next', 'title' : 'Next Page' } ).click(function(){
            
            var current_page = mydoc.data('current_page');
            
            if(current_page < page_count){
            
                current_page++;
            
                renderPage(mydoc.data('pdf'), current_page, canvas.get()[0], mydoc.data('scale'));
                
            }
            
            mydoc.data('current_page', current_page);
            
        });
        
        var but_prev = $('<div>', { 'class' : 'h-pdf-button h-pdf-prev', 'title' : 'Previous Page' } ).click(function(){
            
            var current_page = mydoc.data('current_page');
            
            if(current_page > 1){
                
                current_page--;
                
                renderPage(mydoc.data('pdf'), current_page, canvas.get()[0], mydoc.data('scale'));
            
            }
            
            mydoc.data('current_page', current_page);
            
        });
        
        /*
         * Create the page input
         */
        var page_text = $('<span>', { 'class' : 'h-pdf-pagetext', 'html' : 'Page:' } );
        
        var page_input = $('<input>', { 'type' : 'text', 'class' : 'h-pdf-pageinput', 'value' : settings.page, 'id' : 'h-page-input' } );
        
        page_input.keypress(function(event){
           
           if(event.which == 13){
               
               current_page = $(this).val();
               
               renderPage(mydoc.data('pdf'), current_page, canvas.get()[0], mydoc.data('scale'));
               
               mydoc.data('current_page', current_page);
                
           }else if((event.which < 48 || event.which > 57) && ( event.which != 8 && event.which != 0)){

               return false;
               
           }
            
        });
        
        var of_text = $('<span>', { 'class' : 'h-pdf-pagetext', 'html' : 'of ' });
        
        var pages_text = $('<span>', { 'class' : 'h-pdf-pagecount', 'html' : page_count, 'id' : 'pagecount' });
        
        /*
         * Create the zoom droplist
         */
        var zoomModes = { 3 : '300%', 2 : '200%', 1.5 : '150%', 1 : 'Actual Size', 0.5 : 'Half Size', 0.25 : '25%', 0.1 : '10%' };
        
        var zoom = $('<span>', { 'class' : 'h-pdf-zoom' } );
        
        var zoom_select = $('<select>', { 'class' : 'h-pdf-zoom-select', 'id' : 'page-zoom' } );
        
        zoom.append(zoom_select);
        
        $.each( zoomModes, function(key, value) {
               
            var op = zoom_select.append($("<option></option>").attr("value",key).text(value));
            
        });
        
        zoom_select.change(function(){
           
           var scale = parseFloat($(this).val());
           
           renderPage(mydoc.data('pdf'), mydoc.data('current_page'), canvas.get()[0], scale);
           
           mydoc.data('scale', scale);
        }).val(settings.scale);
        
        /*
         * Add the nav buttons, page input and zoom droplist to the center toolbar
         */
        toolbar_center.append($('<div>', { 'class' : 'h-pdf-toolbar-group' } ).append(but_prev).append(but_next))
            .append(page_text)
            .append(page_input)
            .append(of_text)
            .append(pages_text)
            .append(zoom);
        
        toolbar.append($('<div>', { 'class' : 'h-pdf-toolbar-center-outer' } ).append(toolbar_center));
        
        /*
         * Create the direct download button
         */
        var but_dl = $('<div>', { 'class' : 'h-pdf-button h-pdf-download' } );
        
        but_dl.click(function(){
            
            var delim = '?';
            
            if( url =~ /\?/){
                
                delim = '&';
                
            }
            
            var url = settings.source + delim + "action=download";
            
            window.open(url, '_parent');
            
        });
        
        toolbar_right.append(but_dl);
        
        var resize_canvas = function(){
            
            canvas_container.css('height', mydoc.height() - toolbar.height());
            
        }
        
        resize_canvas();
        
        mydoc.append(canvas_container.append(progress));
        
        var progress = $('<div>', { 'class' : 'h-pdf-progress' } );
        
        progress.css( { top : (canvas_container.height() / 2) - (progress.height() / 2), left : (canvas_container.width() / 2) - (progress.width() / 2) } );
        
        progress.append($('<div>', { 'class' : 'h-pdf-progress-bar' } ).append($('<div>', { 'class' : 'h-pdf-progress-bar-overlay' } )));
        
        canvas_container.append(progress);
        
        PDFJS.getDocument(settings.source).then(
            function getDocumentCallback(pdf) {
        
                canvas_container.html(canvas);
                
                page_count = pdf.numPages;
                
                $('#pagecount').html(page_count);
                
                mydoc.data('pdf', pdf);
    
                renderPage(pdf, settings.page,  canvas.get()[0], settings.scale);
              
            },
            function getDocumentError(message, exception) {
                
                
            },
            function getDocumentProgress(progressData) {
                
                var pct = 100 * (progressData.loaded / progressData.total);
                
                progress.children('div').css('width', pct + '%');
                
            }
        );
        
        this.data('current_page', settings.page);
        
        this.data('scale', settings.scale);
        
        $(window).resize(function(){
            
            resize_canvas();
            
        });
        
        return this;

    };
})( jQuery );
