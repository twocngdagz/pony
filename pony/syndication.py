import time, rfc822

from pony.thirdparty import etree
from pony.thirdparty.etree import Element, SubElement, tostring

from pony.templating import Html, StrHtml

ns = 'http://www.w3.org/2005/Atom'
nsmap = getattr(etree, '_namespace_map', {})
nsmap.setdefault(ns, 'atom')

nsmap_keyargs = {}
if getattr(etree, 'LXML_VERSION', (0, 0, 0, 0)) >= (1, 3, 7, 0):
    nsmap_keyargs = {'nsmap': {'atom':ns}}

def utc(dt):
    if getattr(dt, 'tzinfo', None) is None: return dt
    return dt.replace(tzinfo=None) - dt.utcoffset()

def atom_date(date):
    return utc(date).strftime('%Y-%m-%dT%H:%M:%SZ')

def rss2_date(date):
    return rfc822.formatdate(time.mktime(utc(date).timetuple()))

def atom_author(author):
    if isinstance(author, basestring): author = [ author, None, None ]
    else:
        try: iter(author)
        except TypeError: raise TypeError('Inappropriate author value: %r' % author)
        author = (list(author) + [ None, None ])[:3]
    name, uri, email = author
    result = Element('{http://www.w3.org/2005/Atom}author')
    if name: SubElement(result, '{http://www.w3.org/2005/Atom}name').text = name
    if uri: SubElement(result, '{http://www.w3.org/2005/Atom}uri').text = uri
    if email: SubElement(result, '{http://www.w3.org/2005/Atom}email').text = email
    return result

def rss2_author(author):
    if isinstance(author, basestring): return author
    if len(author) >= 2: return '%s (%s)' % (author[1], author[0])
    return author[0]

def set_atom_text(element, text):
    if isinstance(text, (Html, StrHtml)):
        element.set('type', 'html')
        element.text = text[:]
    elif isinstance(text, basestring):
        element.set('type', 'text')
        element.text = text
    elif hasattr(text, 'makeelement') and getattr(text, 'tag') == '{http://www.w3.org/1999/xhtml}div':
        element.set('type', 'xhtml')
        element.append(text)
    else: raise TypeError('Inappropriate text value: %r' % text)

def set_rss2_text(element, text):
    if hasattr(text, 'makeelement'): element.text = tostring(text)
    elif isinstance(text, basestring): element.text = text[:]

class Feed(object):
    def __init__(feed, title, link, updated,
                 id=None, subtitle=None, feed_link=None, author=None, rights=None,
                 base=None, language=None, icon=None, logo=None):
        feed.link = link
        feed.title = title
        feed.updated = updated
        feed.id = id or feed.link
        feed.subtitle = subtitle
        feed.feed_link = feed_link
        feed.author = author
        feed.rights = rights
        feed.base = base
        feed.language = language
        feed.icon = icon
        feed.logo = logo
        feed.entries = []
    def add(feed, entry):
        feed.entries.append(entry)
    def __str__(feed):
        return tostring(feed.atom())
    def atom(feed, pretty_print=True):
        indent = pretty_print and '\n  ' or ''

        xml = Element('{http://www.w3.org/2005/Atom}feed', **nsmap_keyargs)
        xml.text = indent
        if feed.base: xml.set('{http://www.w3.org/XML/1998/namespace}base', feed.base)
        if feed.language: xml.set('{http://www.w3.org/XML/1998/namespace}lang', feed.language)

        title = SubElement(xml, '{http://www.w3.org/2005/Atom}title')
        set_atom_text(title, feed.title)

        if feed.subtitle:
            subtitle = SubElement(xml, '{http://www.w3.org/2005/Atom}summary')
            set_atom_text(subtitle, feed.subtitle)

        link = SubElement(xml, '{http://www.w3.org/2005/Atom}link', href=feed.link)

        if feed.feed_link:
            feed_link = SubElement(xml, '{http://www.w3.org/2005/Atom}link', rel='self', href=feed.feed_link)

        updated = SubElement(xml, '{http://www.w3.org/2005/Atom}updated')
        updated.text = atom_date(feed.updated)

        id = SubElement(xml, '{http://www.w3.org/2005/Atom}id')
        id.text = feed.id

        if feed.author:
            author = atom_author(feed.author)
            xml.append(author)

        if feed.rights:
            rights = SubElement(xml, '{http://www.w3.org/2005/Atom}rights')
            set_atom_text(rights, feed.rights)

        if feed.icon:
            icon = SubElement(xml, '{http://www.w3.org/2005/Atom}icon')
            icon.text = feed.icon

        if feed.logo:
            logo = SubElement(xml, '{http://www.w3.org/2005/Atom}logo')
            logo.text = feed.logo

        for entry in feed.entries:
            entry_xml = entry.atom(pretty_print)
            entry_xml[-1].tail = indent
            xml.append(entry_xml)

        for child in xml: child.tail = indent   
        xml[-1].tail = pretty_print and '\n' or ''
        return xml
    def rss2(feed, pretty_print=True):
        indent = pretty_print and '\n    ' or ''
        indent2 = pretty_print and '\n      ' or ''

        rss = Element('rss', version='2.0')
        rss.text = pretty_print and '\n  ' or ''

        channel = SubElement(rss, 'channel')
        channel.text = indent
        channel.tail = pretty_print and '\n' or ''

        set_rss2_text(SubElement(channel, 'title'), feed.title)
        set_rss2_text(SubElement(channel, 'description'), feed.subtitle or '')
        SubElement(channel, 'link').text = feed.link
        SubElement(channel, 'lastBuildDate').text = rss2_date(feed.updated)
        if feed.language: SubElement(channel, 'language').text = feed.language
        if feed.rights: SubElement(channel, 'copyright').text = feed.rights
        if feed.logo:
            image = SubElement(channel, 'image')
            image.text = indent2
            SubElement(image, 'url').text = feed.logo
            SubElement(image, 'title').text = ''
            SubElement(image, 'link').text = feed.link
            for child in image: child.tail = indent2
            image[-1].tail = pretty_print and '\n    ' or ''

        for entry in feed.entries:
            item = entry.rss2(pretty_print)
            item[-1].tail = indent
            channel.append(item)

        for child in channel: child.tail = indent
        channel[-1].tail = pretty_print and '\n  ' or ''
        return rss

class Entry(object):
    def __init__(entry, title, link, updated,
                 id=None, summary=None, content=None, published=None,
                 enclosure=None, author=None, rights=None, base=None, language=None):
        entry.link = link
        entry.title = title
        entry.updated = updated
        entry.id = id or entry.link
        entry.summary = summary
        entry.content = content
        entry.published = published
        entry.enclosure = enclosure
        entry.author = author
        entry.rights = rights
        entry.base = base
        entry.language = language
    def __str__(entry):
        return tostring(entry.atom())
    def atom(entry, pretty_print=True):
        indent = pretty_print and '\n    ' or ''

        xml = Element('{http://www.w3.org/2005/Atom}entry', **nsmap_keyargs)
        xml.text = indent
        if entry.base: xml.set('{http://www.w3.org/XML/1998/namespace}base', entry.base)
        if entry.language: xml.set('{http://www.w3.org/XML/1998/namespace}lang', entry.language)

        link = SubElement(xml, '{http://www.w3.org/2005/Atom}link', href=entry.link)

        title = SubElement(xml, '{http://www.w3.org/2005/Atom}title')
        set_atom_text(title, entry.title)

        updated = SubElement(xml, '{http://www.w3.org/2005/Atom}updated')
        updated.text = atom_date(entry.updated)

        id = SubElement(xml, '{http://www.w3.org/2005/Atom}id')
        id.text = entry.id

        if entry.summary:
            summary = SubElement(xml, '{http://www.w3.org/2005/Atom}summary')
            set_atom_text(summary, entry.summary)

        if entry.content:
            content = SubElement(xml, '{http://www.w3.org/2005/Atom}content')
            set_atom_text(content, entry.content)

        if entry.enclosure:
            href, media_type, length = entry.enclosure
            enclosure = SubElement(xml, '{http://www.w3.org/2005/Atom}link',
                                   rel='enclosure', href=href, type=media_type, length=length)

        if entry.author:
            author = atom_author(entry.author)
            xml.append(author)

        if entry.rights:
            rights = SubElement(xml, '{http://www.w3.org/2005/Atom}rights')
            set_atom_text(rights, entry.rights)

        if entry.published:
            published = SubElement(xml, '{http://www.w3.org/2005/Atom}published')
            published.text = atom_date(entry.published)

        for child in xml: child.tail = indent
        xml[-1].tail = pretty_print and '\n' or ''
        return xml
    def rss2(entry, pretty_print=True):
        indent = pretty_print and '\n      ' or ''
        item = Element('item')
        item.text = indent
        set_rss2_text(SubElement(item, 'title'), entry.title)
        set_rss2_text(SubElement(item, 'description'), entry.summary or entry.content)
        SubElement(item, 'link').text = entry.link
        SubElement(item, 'guid', isPermaLink=(entry.id == entry.link and 'true' or 'false')).text = entry.id
        if entry.enclosure:
            href, media_type, length = entry.enclosure
            SubElement(item, 'enclosure', url=href, type=media_type, length=length)
        if entry.author: SubElement(item, 'author').text = rss2_author(entry.author)
        if entry.published: SubElement(item, 'pubDate').text = rss2_date(entry.published)
        for child in item: child.tail = indent
        item[-1].tail = pretty_print and '\n' or ''
        return item