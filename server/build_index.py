import xapian as xa
import os
import json
import gzip
import itertools
from time import time
import indexer as idx
from pprint import pprint

root = os.environ['DATA']

def datasets():
    path = os.path.join(root, 'usertables_schema')
    suffix = '_schema.json'
    for f in sorted(os.listdir(path)):
        if f.endswith(suffix):
            yield f[:-len(suffix)]

def get_schema_content(id):
    path = os.path.join(root, 'usertables_schema', '%s_schema.json' % id)
    with open(path, 'rb') as f:
        return f.read()

def get_data_lines(id, limit=10):
    path = os.path.join(root, 'usertables_data', '%s.json.gz' % id)
    with gzip.open(path, 'r') as f:
        for (i, line) in enumerate(f):
            if limit and i < limit:
                yield line
            else:
                break

if __name__ == '__main__':
    index_data = True

    path = os.path.join(root, 'xapian_index')
    db = xa.WritableDatabase(path, xa.DB_CREATE_OR_OPEN)
    indexer = xa.TermGenerator()

    total = 0
    for _ in datasets():
        total += 1

    start = time()
    for i, id in enumerate(datasets()):
        raw_schema = get_schema_content(id)
        schema = json.loads(raw_schema)
        text = idx.stringify(schema, stemmer=idx.word_stemmer)

        doc = xa.Document()

        # adding terms from schema
        indexer.set_document(doc)
        indexer.index_text(text, 1,'S')

        doc.add_value(0, id)
        doc.add_value(1, raw_schema)

        # adding terms from 
        if index_data:
            lines = list(get_data_lines(id, limit=1000))
            for line in lines:
                data = json.loads(line)
                text = " ".join(str(x) for x in data.values())
                indexer.index_text_without_positions(text, 1, 'D')
            doc.add_value(2, "\n".join(x.decode('utf-8') for x in lines))
        
        db.add_document(doc)
        if i and i % 100 == 0:
            db.commit()
            print("[%d] in %.2f seconds." % (i, time() - start))

    db.commit()
