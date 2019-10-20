#!/usr/bin/env python
# coding: utf-8
import xml.etree.ElementTree as ET
import sys
import string
import re

def parseXML(data_file):
    texts = []
    for record in ET.parse(data_file).getroot().iter("record"):
        date = record.find("header").find("datestamp").text
        date = date.split("-")[0:2]  # Remove day
        meta = record.find("metadata")
        if meta == None:
            continue
        for metadata in meta:
            a = metadata.findall("{http://purl.org/dc/elements/1.1/}creator")
            s = metadata.findall("{http://purl.org/dc/elements/1.1/}subject")
            try:
                if a == None or s == None:
                    # Skip over incomplete papers.
                    continue

                authors = []
                for author in a:
                    if author.text == None:
                        raise ValueError
                    authors.append(author.text)

                topics = []
                for topic in s:
                    if topic.text == None:
                        raise ValueError
                    # Evil trickery to go around arXiv's horrible subject
                    # formatting. This can (obviously) be done better,
                    # but it's fast enough as is.
                    t = topic.text.replace(',', "++")
                    t = re.sub("\(.*\)", "", t)
                    t = re.sub("\n", " ", t)
                    t = re.sub("( )+", " ", t)
                    t = t.strip()
                    ts = t.split("++")
                    for j in ts:
                        topics.append(j.strip())

            except:
                break

        texts.append((date, authors, topics))
    return texts


def formatProperly(texts):
    # Separate each field with '++' and split by this token (and not
    # whitespace) when reading in networkx.

    for (date, authors, topics) in texts:
        # Date T1 T2 T3
        print('-'.join(date), *topics, sep="++")

        # A1 A2 A3 \\ A2 A3
        for j in range(len(authors) - 1):
            print(authors[j], *authors[j+1:], sep="++")

        # T1 T2 T3 \\ T2 T3
        for j in range(len(topics) - 1):
            print(topics[j], *topics[j+1:], sep="++")

        # A1 T1 T2 T3 \\ A2 T1 T2 T3 \\ A3 T1 T2 T3
        for author in authors:
            print(author, *topics, sep="++")


def main(argv):
    if len(argv) < 2:
        print("usage: ./parse-arxiv-xml.py <ArXiv category XML file>")
        exit(1)
    formatProperly(parseXML(argv[1]))


if __name__ == "__main__":
    main(sys.argv)

