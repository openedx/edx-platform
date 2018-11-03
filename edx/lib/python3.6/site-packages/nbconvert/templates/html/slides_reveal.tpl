{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block any_cell scoped -%}
{%- if cell.metadata.get('slide_start', False) -%}
<section>
{%- endif -%}
{%- if cell.metadata.get('subslide_start', False) -%}
<section>
{%- endif -%}
{%- if cell.metadata.get('fragment_start', False) -%}
<div class="fragment">
{%- endif -%}

{%- if cell.metadata.slide_type == 'notes' -%}
<aside class="notes">
{{ super() }}
</aside>
{%- elif cell.metadata.slide_type == 'skip' -%}
{%- else -%}
{{ super() }}
{%- endif -%}

{%- if cell.metadata.get('fragment_end', False) -%}
</div>
{%- endif -%}
{%- if cell.metadata.get('subslide_end', False) -%}
</section>
{%- endif -%}
{%- if cell.metadata.get('slide_end', False) -%}
</section>
{%- endif -%}

{%- endblock any_cell -%}

{% block header %}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<meta http-equiv="X-UA-Compatible" content="chrome=1" />

<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

{% set nb_title = nb.metadata.get('title', '') or resources['metadata']['name'] %}
<title>{{nb_title}} slides</title>

<script src="{{resources.reveal.require_js_url}}"></script>
<script src="{{resources.reveal.jquery_url}}"></script>

<!-- General and theme style sheets -->
<link rel="stylesheet" href="{{resources.reveal.url_prefix}}/css/reveal.css">
<link rel="stylesheet" href="{{resources.reveal.url_prefix}}/css/theme/{{resources.reveal.theme}}.css" id="theme">

<!-- If the query includes 'print-pdf', include the PDF print sheet -->
<script>
if( window.location.search.match( /print-pdf/gi ) ) {
        var link = document.createElement( 'link' );
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = '{{resources.reveal.url_prefix}}/css/print/pdf.css';
        document.getElementsByTagName( 'head' )[0].appendChild( link );
}

</script>

<!--[if lt IE 9]>
<script src="{{resources.reveal.url_prefix}}/lib/js/html5shiv.js"></script>
<![endif]-->

<!-- Loading the mathjax macro -->
{{ mathjax() }}

<!-- Get Font-awesome from cdn -->
<link rel="stylesheet" href="{{resources.reveal.font_awesome_url}}">

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
.reveal {
  font-size: 160%;
}
.reveal pre {
  width: inherit;
  padding: 0.4em;
  margin: 0px;
  font-family: monospace, sans-serif;
  font-size: 80%;
  box-shadow: 0px 0px 0px rgba(0, 0, 0, 0);
}
.reveal pre code {
  padding: 0px;
}
.reveal section img {
  border: 0px solid black;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0);
}
.reveal i {
  font-style: normal;
  font-family: FontAwesome;
  font-size: 2em;
}
.reveal .slides {
  text-align: left;
}
.reveal.fade {
  opacity: 1;
}
.reveal .progress {
  position: static;
}
.reveal .controls .navigate-left,
.reveal .controls .navigate-left.enabled {
  border-right-color: #727272;
}
.reveal .controls .navigate-left.enabled:hover,
.reveal .controls .navigate-left.enabled.enabled:hover {
  border-right-color: #dfdfdf;
}
.reveal .controls .navigate-right,
.reveal .controls .navigate-right.enabled {
  border-left-color: #727272;
}
.reveal .controls .navigate-right.enabled:hover,
.reveal .controls .navigate-right.enabled.enabled:hover {
  border-left-color: #dfdfdf;
}
.reveal .controls .navigate-up,
.reveal .controls .navigate-up.enabled {
  border-bottom-color: #727272;
}
.reveal .controls .navigate-up.enabled:hover,
.reveal .controls .navigate-up.enabled.enabled:hover {
  border-bottom-color: #dfdfdf;
}
.reveal .controls .navigate-down,
.reveal .controls .navigate-down.enabled {
  border-top-color: #727272;
}
.reveal .controls .navigate-down.enabled:hover,
.reveal .controls .navigate-down.enabled.enabled:hover {
  border-top-color: #dfdfdf;
}
.reveal .progress span {
  background: #727272;
}
div.input_area {
  padding: 0.06em;
}
div.code_cell {
  background-color: transparent;
}
div.prompt {
  width: 11ex;
  padding: 0.4em;
  margin: 0px;
  font-family: monospace, sans-serif;
  font-size: 80%;
  text-align: right;
}
div.output_area pre {
  font-family: monospace, sans-serif;
  font-size: 80%;
}
div.output_prompt {
  /* 5px right shift to account for margin in parent container */
  margin: 5px 5px 0 0;
}
div.text_cell.rendered .rendered_html {
  /* The H1 height seems miscalculated, we are just hidding the scrollbar */
  overflow-y: hidden;
}
a.anchor-link {
  /* There is still an anchor, we are only hidding it */
  display: none;
}
.rendered_html p {
  text-align: inherit;
}
::-webkit-scrollbar
{
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar *
{
  background:transparent;
}
::-webkit-scrollbar-thumb
{
  background: #727272 !important;
}
</style>

<!-- Custom stylesheet, it must be in the same directory as the html file -->
<link rel="stylesheet" href="custom.css">

</head>
{% endblock header%}


{% block body %}
{% block pre_slides %}
<body>
{% endblock pre_slides %}

<div class="reveal">
<div class="slides">
{{ super() }}
</div>
</div>
{% block post_slides %}
<script>

require(
    {
      // it makes sense to wait a little bit when you are loading
      // reveal from a cdn in a slow connection environment
      waitSeconds: 15
    },
    [
      "{{resources.reveal.url_prefix}}/lib/js/head.min.js",
      "{{resources.reveal.url_prefix}}/js/reveal.js"
    ],

    function(head, Reveal){

        // Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
        Reveal.initialize({
            controls: true,
            progress: true,
            history: true,

            transition: "{{resources.reveal.transition}}",

            // Optional libraries used to extend on reveal.js
            dependencies: [
                { src: "{{resources.reveal.url_prefix}}/lib/js/classList.js",
                  condition: function() { return !document.body.classList; } },
                { src: "{{resources.reveal.url_prefix}}/plugin/notes/notes.js",
                  async: true,
                  condition: function() { return !!document.body.classList; } }
            ]
        });

        var update = function(event){
          if(MathJax.Hub.getAllJax(Reveal.getCurrentSlide())){
            MathJax.Hub.Rerender(Reveal.getCurrentSlide());
          }
        };

        Reveal.addEventListener('slidechanged', update);

        function setScrollingSlide() {
            var scroll = {{ resources.reveal.scroll | json_dumps }}
            if (scroll === true) {
              var h = $('.reveal').height() * 0.95;
              $('section.present').find('section')
                .filter(function() {
                  return $(this).height() > h;
                })
                .css('height', 'calc(95vh)')
                .css('overflow-y', 'scroll')
                .css('margin-top', '20px');
            }
        }

        // check and set the scrolling slide every time the slide change
        Reveal.addEventListener('slidechanged', setScrollingSlide);

    }

);
</script>

</body>
{% endblock post_slides %}
{% endblock body %}

{% block footer %}
</html>
{% endblock footer %}
