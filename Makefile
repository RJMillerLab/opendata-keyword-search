.PHONY: wordvec index web backend 

DATA = ./data
MODEL=$(DATA)/wordvec/word2vec_50d.txt

backend:
	DATA=$(DATA) WORD2VEC_MODEL=$(MODEL)  python3 server/app.py

frontend:
	cd client && lein figwheel

index:
	rm -rf $(DATA)/xapian_index_$(NAME)
	python3 server/indexer.py --index --index-path $(DATA)/xapian_index_$(NAME) --json $(DATA)/meta_jsons_$(NAME)

wordvec: $(DATA)/wordvec/glove.6B.50d.txt $(DATA)/wordvec/word2vec_50d.txt

$(DATA)/wordvec/glove.6B.zip:
	mkdir -p $(DATA)/wordvec 
	cd $(DATA)/wordvec && wget http://nlp.stanford.edu/data/glove.6B.zip

$(DATA)/wordvec/glove.6B.50d.txt:
	cd $(DATA)/wordvec && unzip glove.6B.zip

$(DATA)/wordvec/word2vec_50d.txt:
	python3 server/wordvec.py \
		--glove $(DATA)/wordvec/glove.6B.50d.txt \
		--model-path $(DATA)/wordvec/word2vec_50d.txt \
		--convert
