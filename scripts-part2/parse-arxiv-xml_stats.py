
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
            date = date[0] + "1"
        else:
            date = date[0] + "2"

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

    time_author_topic = dict()

    for paper in texts:
        (date, authors, topics) = paper
        all_dates.add(date)

        if date not in time_author_topic:
            time_author_topic[date] = dict()
        if date not in time_topic_topic:
            time_topic_topic[date] = dict()



        for author in authors:
            all_authors.add(author)

            if author not in time_author_topic[date]:
                time_author_topic[date][author] = dict()

            for topic in topics:
                if topic == "":
                    continue
                all_topics.add(topic)
                if topic not in time_author_topic[date][author]:
                    time_author_topic[date][author][topic] = 1
                else:
                    time_author_topic[date][author][topic] += 1


        for topic_pair in [(t1, t2) for t1 in topics for t2 in topics]:
            if topic_pair not in time_topic_topic[date]:
                time_topic_topic[date][topic_pair] = 1
            else:
                time_topic_topic[date][topic_pair] += 1


    la = len(all_authors)
    ld = len(all_dates)
    lt = len(all_topics)

    print("Total authors:", la)
    print("Total dates:", ld)
    print("Total topics:", lt)
    print("Total topic x author pairs:", lt * la)
    print("Total topic x topic pairs:", lt * lt)

    return
    den = len(all_author_topic_pairs)

    jat_tensor = open("time_author_topic.txt", 'w')
    jat_tensor.write("Total Times:\t" + str(len(all_dates)) + '\n')
    jat_tensor.write("Total Samples:\t" + str(len(all_topics)) + '\n')
    jat_tensor.write("Total Genes:\t" + str(len(all_authors)) + '\n')
    for time in all_dates:
        jat_tensor.write("Time\t" + str(time) + '\n')
        jat_tensor.write("ID\tNAME")
        for topic in all_topics:
            jat_tensor.write('\t' + topic)
        jat_tensor.write('\n')
        for (index, author) in enumerate(all_authors):
            jat_tensor.write(str(index) + '\t' + author)
            for topic in all_topics:
                if author in time_author_topic[time] and topic in time_author_topic[time][author]:
                    jat_tensor.write('\t' + str((time_author_topic[time][author][topic] + 1) / den))
                else:
                    jat_tensor.write("\t" + str(1 / den))
            jat_tensor.write('\n')


    return

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

