from django import template
from django.template import Template

register = template.Library()


@register.simple_tag(takes_context=True)
def sso_meta(context):
    return Template('<meta name="title" content="${ title }">' + ' ' +
                    '<meta name="description" content="${ subtitle }">' + ' ' +
                    ## OG (Open Graph) title and description added below to give social media info to display
                    ## (https://developers.facebook.com/docs/opengraph/howtos/maximizing-distribution-media-content#tags)

                    '<meta property="og:title" content="${ title }">' + ' ' +
                    '<meta property="og:description" content="${ subtitle }">' + ' ' +
                    '<meta prefix="og: http://ogp.me/ns#" name="image" property="og:image" content="${ banner_image[\'large\'][\'url\'] }">' + ' ' +
                    '<meta property="og:image:width" content="512">' + ' ' +
                    '<meta property="og:image:height" content="512">' + ' ' +
                    '<meta name="twitter:image" content="${ banner_image[\'large\'][\'url\'] }">' + ' ' +

                    '<meta name="twitter:card" content="${ banner_image[\'large\'][\'url\'] }">' + ' ' +
                    '<meta name="twitter:site" content="@PhilanthropyUni">' + ' ' +
                    '<meta name="twitter:title" content="${ title }">' + ' ' +
                    '<meta name="twitter:description" content="${ subtitle }">').render(context);

