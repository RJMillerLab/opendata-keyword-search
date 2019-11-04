# Keyword search of Open Data

This is the repository for a keyword search engine for Open Data repositories.

The implementation is based :

- [Xapian](https://xapian.org/): a high performant and scalable text search engine.
- [Gensim](https://radimrehurek.com/gensim/): a Python NLP library.  This is
  used to access pretrained word vectors.

The search engine indexes and searches both metadata and data values of
[Socrata](https://dev.socrata.com/data/) data sets.

## Prerequisites:

- Socrata datasets:
    - Data files: `./data/usertables_data/<package_id>.json.gz
    - Metadata files: `./data/usertables_schema/<package_id>_schema.json`

- Pretrained GloVe word vectors

## Makefile

`make ./data/wordvec/glove.6B.txt`

> Downloads the glove vectors

`make ./data/wordvec_50d.txt`

> converts the glove vectors to word2vec vectors

`make index`

> Creates the xapian index for both metadata and data values.

`make backend`

> Starts the backend search API server

`make frontend`

> Starts the frontend Web application at port 8997.
> You can start searching at "http://localhost:8997"
