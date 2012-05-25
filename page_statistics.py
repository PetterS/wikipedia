#!/usr/bin/python

# Petter Strandmark 2012
#
# The command
#    page_statistics.py svwiki-20120514-pages-meta-current.xml.bz2
# Will generate a list of the 1000 most wanted pages for that data dump
# and a list of pages without any links
#

import sys
import optparse
import os.path
import cPickle as pickle
import xml.etree.cElementTree as ElementTree
from bz2 import BZ2File
import re
from string import upper, strip

usage = "usage: %prog [options] database.xml.bz2"
parser = optparse.OptionParser(usage)
parser.add_option("-n", "--n_output", help="Number of pages to output", type=int, default=1000)
parser.add_option("-x", "--limit", help="Limit the number of articles (debug)", type=int, default=-1)
parser.add_option("-l", "--links", help="How to translate the word 'links'", type=str, default="links")
(options, args) = parser.parse_args() 

filename = 'svwiki-20120514-pages-meta-current.xml.bz2'
if len(args) > 0 :
    filename = args[0]
    
datafilename = filename + '.cache'
wantedpagesfilename = filename + '.wanted.wiki'
nolinkpagesfilename = filename + '-nolink.wiki'
headerfilename = '.header.wiki'
footerfilename = '.footer.wiki'

ignored_prefixes = ['File:', 'Fil:', 'Bild:', 'Image:', 'Kategori:', ':Kategori:', ':src:', 'Wikt:']
def is_page(page) :
    for prefix in ignored_prefixes : 
        if page.startswith(prefix) :
            return False
    # Avoid interwiki links
    if len(page)>3 and page[2]==':' :
        return False
    if len(page)>4 and page[3]==':' :
        return False
    if len(page)>4 and page[0]==':' and page[3]==':' :
        return False
    return True

if not os.path.exists(datafilename) :
    print 'Parsing compressed XML file...'
    
    file = BZ2File(filename,'r')

    wikilink = re.compile(r'\[\[(.*?)\]\]')

    all_pages = dict()
    nolink_pages = list()
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
            # Replace '_' with ' '
            title = title.replace('_',' ')
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
                this_page_has_link = False
                for link in links :
                    # Does the link contain a '|'?
                    p = link.find('|') 
                    if p >= 0 : 
                        link = link[:p]
                    
                    # Does the link contain a '#'?
                    p = link.find('#') 
                    if p >= 0 : 
                        link = link[:p]

                    # Make first character upper case
                    if len(link) > 0 :
                        link = upper(link[0]) + link[1:]
                        
                    # Replace '_' with space
                    link = link.replace('_',' ')
                    
                    # Strip white space
                    link = strip(link)
                    
                    # Is it still a valid link?
                    if len(link) > 0 :
                        this_page_has_link = True
                    
                    # If this link is a link to a page and not already on this page
                    if len(link)>0 and is_page(link) and not links_on_page.has_key(link) :
                        links_on_page[link] = 1
                        # Does this link exist in the dictionary?
                        if number_of_links.has_key(link) :
                            number_of_links[link] += 1
                        else :
                            number_of_links[link] = 1
                
                if not this_page_has_link:
                    nolink_pages.append(title)
                
            elem.clear()
            
        # Print some progress every now and then
        iterations+=1
        if iterations % 10000 == 0 :
            sys.stdout.write('\r')
            sys.stdout.write('%.1f MB, %d kpages processed.  (%d XML events)                   ' % (float(file.tell())/1024**2, len(all_pages)//1000, iterations) )
            if options.limit > 0 and len(all_pages) >= options.limit :
                break
            
    print ''
            
    # Remove all existing pages and pages with less than 2 links
    print 'Removing existing pages...'
    new_number_of_links = dict()
    for page in number_of_links.iterkeys() :
        if not all_pages.has_key(page)  and number_of_links[page] >= 2:
            new_number_of_links[page] = number_of_links[page]
    
    # Create a sorted list
    print 'Sorting...'
    sorted_links = sorted( new_number_of_links, key=new_number_of_links.get, reverse=True)
    
    # Save to cache file
    print 'Creating cache file...'
    with open(datafilename, 'wb') as f:
        pickle.dump(new_number_of_links,f)
        pickle.dump(sorted_links,f)
        pickle.dump(nolink_pages, f)
    
else :
    print 'Reading cache file...'
    with open(datafilename, 'rb') as f:
        number_of_links = pickle.load(f)
        sorted_links = pickle.load(f)
        nolink_pages = pickle.load(f)
    
    
    
def add_file_to_file(output, filename_to_add) :
    if os.path.exists(filename_to_add) :
        with open(filename_to_add,'r') as f: 
            output.write(f.read())
    
#
# Wanted pages
#
n_printed = 0
output = open(wantedpagesfilename, 'w')
add_file_to_file(output, 'wantedpages' + headerfilename)
# Write list of pages
for page in sorted_links :
    str = '#[[%s]]: [[Special:Whatlinkshere/%s|%d %s]]\n' % (page, page, number_of_links[page], options.links)
    output.write(str.encode('utf8'))

    n_printed += 1
    if n_printed >= options.n_output :
        break
        
add_file_to_file(output, 'wantedpages' + footerfilename)
output.close()

#
# Pages with no links
#
output = open(nolinkpagesfilename, 'w')
add_file_to_file(output, 'nolinkpages' + headerfilename)
for page in nolink_pages :
    str = '#[[%s]]  \n' % (page, )
    output.write( str.encode('utf8') )
add_file_to_file(output, 'nolinkpages' + footerfilename)

print nolink_pages