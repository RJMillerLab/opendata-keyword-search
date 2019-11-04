from flask import Flask, request, render_template, g
from flask_cors import CORS
import os
import indexer
import wordvec
import xapian
import logging
from time import time

DATA = os.environ['DATA']
MODEL = os.environ['WORD2VEC_MODEL']

def xapian_database():
    if 'db' not in g:
        path = os.path.join(DATA, 'xapian_index')
        g.db = xapian.Database(path)
    return g.db

def load_model():
    print("[Loading word2vec model]")
    start = time()
    model = wordvec.load_model(MODEL)
    print("\t loaded in %.2f seconds" % (time() - start))
    return model

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
cors = CORS(app)
word2vec_model = load_model()

@app.route("/")
def Index():
    return "This is the search engine backend"

@app.route("/search")
def Search():
    q = request.args.get('q', "").strip()
    expand = request.args.get('expand')
    offset = request.args.get('offset')
    limit = request.args.get('limit')
    prefix = request.args.get('prefix', 'S')

    try:
        offset = int(offset)
    except:
        offset = None

    try:
        limit = int(limit)
    except:
        limit = None

    if not q:
        return dict(error="Empty query")
    else:
        if expand:
            expand_args = dict(model=word2vec_model, threshold=0.7)
        else:
            expand_args = None

        return indexer.query(xapian_database(), 
                q, 
                prefix,
                offset, limit, 
                expand_args)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8998, debug=True)
