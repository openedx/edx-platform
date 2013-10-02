import requests
from requests.exceptions import ConnectionError
import lxml
import lxml.html
from lxml.cssselect import CSSSelector

from py2neo import neo4j

db = neo4j.GraphDatabaseService(neo4j.DEFAULT_URI)

def _grab_article_links(relative_url):
    """
    Given a relative Wikipedia article url, will grab all links within that article
    """

    wikipedia_url = "http://www.wikipedia.org%s" % relative_url
    page = requests.get(wikipedia_url).content
    selector = CSSSelector('a')
    html = lxml.html.fromstring(page)
    links = [item.get('href', "") for item in selector(html)]
    articles = set(link for link in links if _is_an_article(link))
    return articles


def _is_an_article(link):
    """
    Given a link from a page, determines whether or not the link is to another wikipedia article
    """
    on_wikipedia = link.startswith("/wiki/")
    # Wikipedia uses the colon as a reserved pseudo-mimetype indicator for non-articles
    is_not_reserved_page = not ":" in link
    is_not_main_page = not link.endswith("/Main_Page")
    return on_wikipedia and is_not_reserved_page and is_not_main_page


def _create_node_from_article(link, index):
    """
    Given the href stub and the index to be inserted into, update the database to 
    """

    absolute_url = "http://www.wikipedia.org%s" % link
    try:
        article = lxml.html.fromstring(requests.get(absolute_url).content)
    except ConnectionError:
        article = lxml.html.fromstring(requests.get(absolute_url).content)
    selector = CSSSelector('#firstHeading span')
    title = selector(article)[0].text_content()
    return index.get_or_create("title", title, {"title": title, "url": absolute_url})

def _add_all_nodes_to_neo4j(base_link, index):
    """
    Given a base link, adds all nodes representing articles linked to from that base linke to neo4j
    """

    node_index = db.get_or_create_index(neo4j.Node, index)
    base_node = _create_node_from_article(base_link, node_index)
    print base_link
    for link in _grab_article_links(base_link):
        print link
        current_node = _create_node_from_article(link, node_index)
        db.get_or_create_relationships((base_node, "LINKS_TO", current_node))

def _extend_node_mapping(base_link, index):
    """
    Given a base link, scrapes all nodes linked to that node and adds the information to the database.

    Worth noting that this is likely to be pretty slow.
    """

    node_index = db.get_or_create_index(neo4j.Node, index)
    base_node = _create_node_from_article(base_link, node_index)
    relative_url = lambda absolute_url: "/%s/%s" % (absolute_url.split("/")[-2], absolute_url.split("/")[-1])
    for relationship in base_node.match(bidirectional=True):
        linked_node = relationship.end_node
        _add_all_nodes_to_neo4j(relative_url(linked_node["url"]), index)

_extend_node_mapping("/wiki/Science", "article")