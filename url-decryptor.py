#! python3
'''
DESCRIPTION:
This script will take a URL of a specific online-magazine's paywall-ed content, decrypt it and write the site's content to a local HTML file.

DISCLAIMER:
This is a theoretical exercise only and must not be used to access paid-only content.
'''

import requests, os, bs4, sys

# TODO
# implement a basic GUI
# Add some basic CSS to the file
# Retrieve pictures?
# File encoding might be wonky

def parse(page):
    """

    :param page: URL with rot-25 obfuscated content
    :type page: bs4-object
    :return: page with decrypted content
    :rtype: list of strings
    """
    output = []
    output.append(page.select('span.headline-intro')[0].get_text())
    output.append(page.select('span.headline')[0].get_text())
    output.append(page.select('p.article-intro')[0].get_text())
    p_all = page.select(".column-both-center p") # As there's no straightforward way to separate readable content from the obfuscated one, gather all <p> first
    for p in p_all: # Now loop through them, but stop once we hit the obfuscated content, thus only readable <p> are added to the content list
        text = p.get_text()
        if p.get('class') is None and text is not None:
            if (p.parent in page.select('noscript')): # The noscript parent indicates the beginning of the obfuscated content, thus we can stop the loop here
                break
            else:
                output.append(text)
    p_obfuscated = page.select('p.obfuscated') # To make things easier, a new list containing only the obfuscated <p> is created

    for p in p_obfuscated:
        p_txt = p.get_text()

        # This is a fun one: For some reason hyperlinks within the obfuscated sections are not obfuscated, but instead normal clear-text.
        # Running the clear-text through the rot-n decryption obviously produces garbage, so this work-around is required:
        # First check if there are any hyperlinks within the current tag, then extract the text within the hyperlink, it's starting index within the paragraph's string and it's length
        # Using these three values a range can be created, which is passed to the make_readable function. Letters within this range will subsequently be ignored when decrypting.
        ignore_range = []
        if len(p.select('a')) > 0:
            links = p.select('a')
            for a in links:
                link_text = a.get_text()
                index = p_txt.find(link_text)
                ignore_range = range(index,(index+len(link_text)))

        p_readable = make_readable(p_txt, ignore_range)
        output.append(p_readable)
    return output

def make_readable(p_txt, ignore_range):
    """

    :param p_txt: rot-25 obfuscated text
    :type p_txt: string
    :param ignore_range: range of letters within p_txt to ignore
    :type ignore_range: list
    :return: decrypted text
    :rtype: string
    """

    rot = 27 # Why do I need to use 27 instead of 25, if it's a rot-25 cypher???
    s = ''
    for i, l in enumerate(p_txt):
        if len(l) != 1 or l == ' ' or i in ignore_range:
            s += l

        # All letters and alphanumericals are shifted according to the rot-value
        else:
            l.lower()
            v = (ord(l) - rot)
            if v > ord('z'):
                v -= 26
            else:
                v += 26
            if v > 122:
                 v += 52
            s += chr(v)
    return s

def make_readable_alt(p_txt):
    '''
    Makes a rot-25 obfuscated string readable again (alternative version)
    source: https://gist.github.com/inaz2/9a1abd63abbf1807058b
    '''

    rot = 25
    s = bytearray(p_txt, encoding='UTF-8')
    for i, c in enumerate(s):
        if 0x41 <= c <= 0x5a:
            s[i] = ((c - 0x41 + rot) % 0x1a) + 0x41
        elif 0x61 <= c <= 0x7a:
            s[i] = ((c - 0x61 + rot) % 0x1a) + 0x61
    s = bytes(s).decode(encoding='utf-8')

    return s

def write_file(output):
    """

    :param output: text to write to file
    :type output: list of strings/<p>aragraphs
    """
    file_name = (output[0] + '.html')
    working_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    file = open(os.path.join(working_dir, file_name), 'w')
    file.write('<html><body>')
    for line in output:
        file.write('<p>' + line + '</p>')
    file.write('</body></html>')
    file.close()

def main():
    url = input('Enter the URL:\n')
    r = requests.get(url)
    try:
        r.raise_for_status()
    except Exception as exc:
        print('URL could not be retrieved with error: %s' % (exc))
    page = bs4.BeautifulSoup(r.text, "html.parser")
    output = parse(page)
    write_file(output)

main()