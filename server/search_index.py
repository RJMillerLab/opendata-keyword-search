import xapian as xa
import indexer as idx
import os
import sys
from pprint import pprint

root = os.environ['DATA']

path = os.path.join(root, 'xapian_index')

db = xa.Database(path)

prefix = sys.argv[1]
query_string = " ".join(sys.argv[2:])

pprint(idx.query(db, query_string, prefix, 0, 10, expand_args=None))
