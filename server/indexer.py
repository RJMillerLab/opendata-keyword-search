import json
import argparse
import re
import os
import xapian
from pprint import pprint
from time import time
import wordvec
import logging as log


def flat(data, path):
    "flattens the data into a list of path, value"
    result = []
    if not data:
        pass
    elif isinstance(data, list):
        for (i, x) in enumerate(data):
            result.extend(flat(x, path + [i]))
    elif isinstance(data, dict):
        for (k, v) in data.items():
            result.extend(flat(v, path + [str(k)]))
    else:
        result.append((path, str(data)))

    return result


def word_stemmer(x):
    return re.sub(r'\W+', ' ', x)

def stringify(data, stemmer=None, include_path=False):
    stemmer = stemmer or str
    terms = []
    for path, value in flat(data, []):
        if include_path:
            for p in path:
                if isinstance(p, str):
                    terms.append(p)
        terms.append(stemmer(value))

    return " ".join(terms)

def get_query_phrases(query):
    typ = query.get_type()

    if type == query.OP_OR:
        q1 = get_query_phrases(query.get_subquery(0))
        q2 = get_query_phrases(query.get_subquery(1))
        return q1 + q2
    elif type == query.OP_PHRASE:
        return [" ".join(x.decode('utf-8') for x in list(query))]
    else:
        return [x.decode('utf-8') for x in list(query)]

def matched(row, terms):
    for v in row.values():
        v = str(v).lower()
        for term in terms:
            if term in v:
                return True
    return False

def query(database, query_string, prefix, offset, limit, expand_args):
    offset = offset or 0
    limit = limit or 10

    enquire = xapian.Enquire(database)

    parser = xapian.QueryParser()
    parser.set_database(database)


    synonym = None
    query_terms = [x for x in re.split(r'\W+', query_string) if x]
    if expand_args:
        query_terms, synonym = wordvec.expand(query_terms, **expand_args)

    query = parser.parse_query(" ".join(query_terms),
            xapian.QueryParser.FLAG_DEFAULT,
            prefix)

    enquire.set_query(query)
    matches = enquire.get_mset(offset, limit)

    entries = []
    for m in matches:
        entry = dict(rank=m.rank, 
                dataset_id=m.document.get_value(0).decode('utf-8'),
                docid=m.docid,
                percent=m.percent,
                search_prefix=prefix)
        entry['schema'] = m.document.get_value(1).decode('utf-8')

        if prefix == 'D':
            rows_string = m.document.get_value(2).decode('utf-8')
            table = []
            for row_string in rows_string.split("\n\n"):
                row = json.loads(row_string)
                if matched(row, query_terms):
                    table.append(row)
                    if len(table) >= 20:
                        break

            entry['table'] = json.dumps(table)

        entries.append(entry)

    return dict(
            entries=entries,
            query=query_terms,
            synonym=synonym,
            offset=offset,
            limit=limit,
            total=matches.get_matches_estimated())
