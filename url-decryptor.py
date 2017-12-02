#! python3
'''
DESCRIPTION:
This script will take a URL of a specific online-magazine's paywall-ed content, decrypt it and write the site's content to a local HTML file.

DISCLAIMER:
This is a theoretical exercise only and must not be used to access paid-only content.
'''

import requests, os, bs4, sys, argparse

# TODO
# implement a basic GUI
# Add some basic CSS to the file
# Retrieve pictures?
# File encoding might be wonky
# Properly check upper & lower cases in make_readable

def parse_header(page):
    classes = ['span.headline-intro','span.headline','p.article-intro']
    for c in classes:
        yield page.select(c)[0].get_text()

def parse_body(page):
    p_all = page.select(".column-both-center p")  # As there's no straightforward way to separate readable content from the obfuscated one, gather all <p> first
    for p in p_all: # Now loop through them, but stop once we hit the obfuscated content, thus only readable <p> are added to the content list
        text = p.get_text()
        if p.get('class') is None and text is not None:
            if (p.parent in page.select('noscript')): # The noscript parent indicates the beginning of the obfuscated content, thus we can stop the loop here
                break
            else:
                yield text

def parse_encrypted(page):
    # To make things easier, a new list containing only the obfuscated <p> is created
    p_obfuscated = page.select('p.obfuscated')

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

        yield p_readable

def parse_page(page):
    output = []
    generators = [parse_header(page), parse_body(page), parse_encrypted(page)]

    for gen in generators:
        try:
            while True:
                output.append(next(gen))
        except StopIteration:
            pass

    return output

def make_readable(p_txt, ignore_range):
    """
    This function takes a rot-25 obfuscated string, shifts it accordingly and returns the deciphered string.

    :param p_txt: rot-25 obfuscated text
    :type p_txt: string
    :param ignore_range: range of letters within p_txt to ignore
    :type ignore_range: list
    :return: decrypted text
    :rtype: string
    """

    rot = 27 # Why do I need to use 27 instead of 25, if it's a rot-25 cypher?
    s = '' # The deciphered string

    # Enumerate the encrypted string, shifting one letter or symbol each step
    for i, l in enumerate(p_txt):
        if len(l) != 1 or l == ' ' or i in ignore_range: # Ignore Whitespaces or the letters within the given ignore_range, as they are already decrypted (see comments in parse function)
            s += l # Ignored symbols/letters are added directly to the deciphered string

        # All letters and alphanumericals that are not ignored are then shifted according to the rot-value
        else:
            v = (ord(l) - rot) # Translate the encrypted letter into an integer (using ord), representing it's ASCII value; then subtract the rot-value (i.e. shifting n steps on the ASCII table) to receive it's decrypted counterpart

            # As the ASCII table contains more symbols than just the alphabet, the following ensures the decrypter 'wraps around' the end/beginning of the alphabet
            if v > ord('z'):
                v -= 26
            else:
                v += 26

            # Certain alphanumerical symbols and special letters are encrypted as well and represent edge case. They need to be shifted further 52 steps on the ASCII table to be decrypted properly.
            if v > 122:
                 v += 52

            s += chr(v)      # Translate the ASCII value back into a letter, and add it to the output string
    return s

def make_readable_alt(p_txt):
    '''
    Makes a rot-25 obfuscated string readable (alternative version)
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
    file = open(os.path.join(working_dir+'\output', file_name), 'w')
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
    else:
        page = bs4.BeautifulSoup(r.text, "html.parser")
        output = parse_page(page)
        write_file(output)

main()