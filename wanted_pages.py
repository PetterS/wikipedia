# Petter Strandmark 2012

import sys
import optparse
import xml.etree.cElementTree as ElementTree
from bz2 import BZ2File
import re
import operator
from string import upper

usage = "usage: %prog [options] database.xml.bz2"
parser = optparse.OptionParser(usage)
(options, args) = parser.parse_args() 

filename = 'svwiki-20120514-pages-meta-current.xml.bz2'
if len(args) > 0 :
    filename = args[0]

file = BZ2File(filename,'r')

wikilink = re.compile(r'\[\[(.*?)\]\]')

all_pages = dict()
number_of_links = dict()

iterations = 0
title = ''
text = ''
ns = ''
for event, elem in ElementTree.iterparse(file, events=('start', 'end')):
    #Remove "{extra}" from "{extra}tag"
    tag = elem.tag[ elem.tag.find('}') + 1: ]
    #print event, tag
    if event == 'start' and tag == 'page' :
        title = ''
        text = ''
        ns = ''
        links_on_page = dict()
    elif event == 'end' and tag == 'title' :
        title = elem.text
        elem.clear()
    elif event == 'end' and tag == 'text' :
        text = elem.text
        elem.clear()
    elif event == 'end' and tag == 'ns' :
        ns = elem.text
        elem.clear()
    elif event == 'end' and tag == 'page' :
        
        # Add to pages dictionary
        all_pages[title] = 1
        
        # Only work in main name space
        if ns == '0':
            #Extract everything between [[ ]] tags
            links = wikilink.findall(text)
            for link in links :
                # Does the link contain a '|'?
                p = link.find('|') 
                if p >= 0 : 
                    link = link[:p]
            
                # First character upper case
                if len(link) > 0 :
                    link = upper(link[0]) + link[1:]
            
                # If this link is not already on this page
                if not links_on_page.has_key(link) :
                    links_on_page[link] = 1
                    # Does this link exist in the dictionary?
                    if number_of_links.has_key(link) :
                        number_of_links[link] += 1
                    else :
                        number_of_links[link] = 1
            
        elem.clear()
        
    # Print some progress every now and then
    iterations+=1
    if iterations % 10000 == 0 :
        sys.stdout.write('\r')
        sys.stdout.write('%d pages processed.  (%d XML events)            ' % (len(all_pages), iterations) )
        
print ''
        
sorted_links = sorted( number_of_links, key=number_of_links.get, reverse=True)

for i in range(100) :
    page = sorted_links[i]
    
    # Does this page exist?
    if not all_pages.has_key(page) :
        try :
            print page,
        except UnicodeEncodeError:
            print '<unicode>',
        print ':', number_of_links[page]
    
