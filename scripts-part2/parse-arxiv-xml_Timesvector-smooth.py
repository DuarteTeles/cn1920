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
        date = date.split("-")

        # Collapse day and month into semesters (6 months).
        if int(date[1]) <= 6:
            date = date[0] + "1sem"
        else:
            date = date[0] + "2sem"

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
                    authors.append(author.text.replace(" ", "+"))

                topics = []
                for topic in s:
                    if topic.text == None:
                        raise ValueError
                    # Evil trickery to go around arXiv's horrible subject
                    # formatting. This can (obviously) be done better,
                    # but it's fast enough as is.
                    t = ""
                    if topic.text[0].isdigit() and topic.text[1].isdigit() and topic.text[2].isalpha() and topic.text[3].isdigit() and topic.text[4].isdigit():
                        #print("before:", topic.text)
                        t = topic.text.replace(", ", ",")
                        t = t.replace(" ", ",")
                        #print("after:", t)
                    if t != "":
                        t = t.replace(',', "++")
                    else:
                        t = topic.text.replace(',', "++")
                    t = re.sub("\(.*\)", "", t)
                    t = re.sub("\n", " ", t)
                    t = re.sub("[pP]rimary:?", " ", t)
                    t = re.sub("[sS]econd?ary:?", " ", t)
                    t = re.sub(R"\sep", " ", t)
                    t = re.sub("and", " ", t)
                    t = re.sub("( )+", " ", t)
                    t = t.strip()
                    ts = t.split("++")

                    topics.extend([re.sub(" ","+", x.strip()) for x in ts])
                    #for j in ts:
                    #    topics.append(j.strip())

            except:
                break

        texts.append((date, authors, topics))
    return texts


def buildDictionaries(texts):
    time_topic_topic = dict()
    time_author_author = dict()
    author_topic_time = dict()

    all_topics = set()
    all_dates = set()
    all_authors = set()

    def printTuple(pair):
        return pair[0] + '_' + pair[1]

    for paper in texts:
        (date, authors, topics) = paper
        all_dates.add(date)

        for author in authors:
            all_authors.add(author)
            if author not in author_topic_time:
                author_topic_time[author] = dict()

            for topic in topics:
                if topic == "":
                    continue
                all_topics.add(topic)
                if (date, topic) not in author_topic_time[author]:
                    author_topic_time[author][(topic, date)] = 1
                else:
                    author_topic_time[author][(topic, date)] += 1


        if date not in time_topic_topic:
            time_topic_topic[date] = dict()
        for topic_pair in [(t1, t2) for t1 in topics for t2 in topics]:
            if topic_pair not in time_topic_topic[date]:
                time_topic_topic[date][topic_pair] = 1
            else:
                time_topic_topic[date][topic_pair] += 1

        if date not in time_author_author:
            time_author_author[date] = dict()
        for author_pair in [(a1, a2) for a1 in authors for a2 in authors]:
            if author_pair not in time_author_author[date]:
                time_author_author[date][author_pair] = 1
            else:
                time_author_author[date][author_pair] += 1

    all_topic_time_pairs = [(t, d) for t in all_topics for d in all_dates]
    all_topic_topic_pairs = [(t1, t2) for t1 in all_topics for t2 in all_topics]
    #all_author_author_pairs = [(a1, a2) for a1 in all_authors for a2 in all_authors]

    print("Total authors:", len(all_authors))
    print("Total dates:", len(all_dates))
    print("Total topics:", len(all_topics))
    print("Total topic x time pairs:", len(all_topic_time_pairs))
    print("Total topic x topic pairs:", len(all_topic_topic_pairs))
    #print("Total author x author pairs:", len(all_author_author_pairs))

    wrote_authors = 0
    wrote_tj_pair = 0
    wrote_tj_pair_header = 0
    atj_tensor = open("author_topic_time.txt", 'w')
    atj_tensor.write("ID")
    for topic_time_pair in all_topic_time_pairs:
        wrote_tj_pair_header += 1
        atj_tensor.write('\t' + printTuple(topic_time_pair))
    atj_tensor.write('\n')
    for author in all_authors:
        atj_tensor.write(author)
        wrote_authors += 1
        for topic_time_pair in all_topic_time_pairs:
            wrote_tj_pair += 1
            if topic_time_pair in author_topic_time[author]:
                atj_tensor.write('\t' + str((author_topic_time[author][topic_time_pair]+1)/ len(all_topic_time_pairs)))
            else:
                atj_tensor.write('\t' + str(1/len(all_topic_time_pairs)))
        atj_tensor.write('\n')
        assert wrote_tj_pair == wrote_tj_pair_header
        wrote_tj_pair = 0
    atj_tensor.close()
    assert wrote_authors == len(all_authors)
    print("Wrote atj tensor")

    wrote_time = 0
    wrote_tt_pair = 0
    wrote_tt_pair_header = 0
    jtt_tensor = open("time_topic_topic.txt", 'w')
    jtt_tensor.write("ID")
    for topic_topic_pair in all_topic_topic_pairs:
        wrote_tt_pair_header += 1
        jtt_tensor.write('\t' + printTuple(topic_topic_pair))
    jtt_tensor.write('\n')
    for time in all_dates:
        wrote_time += 1
        jtt_tensor.write(time)
        for topic_topic_pair in all_topic_topic_pairs:
            wrote_tt_pair += 1
            if topic_topic_pair in time_topic_topic[time]:
                jtt_tensor.write('\t' + str(time_topic_topic[time][topic_topic_pair]))
            else:
                jtt_tensor.write('\t0')
        jtt_tensor.write('\n')
        assert wrote_tt_pair == wrote_tt_pair_header
        wrote_tt_pair = 0
    jtt_tensor.close()
    assert wrote_time == len(all_dates)
    print("Wrote jtt tensor")

   # wrote_time = 0
   # wrote_aa_pair = 0
   # wrote_aa_pair_header = 0
   # jaa_tensor = open("time_author_author.txt", 'w')
   # jaa_tensor.write("ID")
   # for author_author_pair in all_author_author_pairs:
   #     wrote_aa_pair_header += 1
   #     jaa_tensor.write('\t' + printTuple(author_author_pair))
   # jaa_tensor.write('\n')
   # for time in all_dates:
   #     jaa_tensor.write(time)
   #     wrote_time += 1
   #     for author_author_pairs in all_author_author_pairs:
   #         wrote_aa_pair += 1
   #         if author_author_pair in time_author_author[time]:
   #             jaa_tensor.write('\t' + str(time_author_author[time][author_author_pair]))
   #         else:
   #             jaa_tensor.write('\t0')
   #     jaa_tensor.write('\n')
   #     assert wrote_aa_pair == wrote_aa_pair_header
   #     wrote_aa_pair = 0
   # jaa_tensor.close()
   # assert wrote_time == len(all_dates)
   # print("Wrote jaa tensor")




    pass


def main(argv):
    if len(argv) < 2:
        print("usage: ./parse-arxiv-xml.py [<ArXiv category XML file>]+")
        exit(1)

    all_texts = []
    for collection in argv[1:]:
        all_texts.extend(parseXML(collection))

    buildDictionaries(all_texts)


if __name__ == "__main__":
    main(sys.argv)

