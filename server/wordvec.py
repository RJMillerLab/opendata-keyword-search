import argparse
from gensim.models import KeyedVectors

def load_model(model_path):
    if model_path:
        return KeyedVectors.load_word2vec_format(model_path, binary=False)
    else:
        return None

def expand(words, model=None, threshold=0.7, max_expansion=3):
    if not model:
        return words, []

    result = [] 
    synonym = dict()
    for w in words:
        result.append(w)
        i = 0
        try:
            for (w_sim, score) in model.most_similar(positive=[w], topn=10):
                if score >= threshold:
                    i += 1
                    result.append(w_sim)
                    synonym[w_sim] = w
                if i >= max_expansion:
                    break
        except KeyError:
            pass

    return result, list(synonym.items())


if __name__ == '__main__':
    from gensim.scripts.glove2word2vec import glove2word2vec

    parser = argparse.ArgumentParser()

    parser.add_argument('--glove')
    parser.add_argument('--model-path')

    parser.add_argument('--convert', action='store_true')
    parser.add_argument('--query', action='store_true')
    parser.add_argument('terms', nargs='*')

    args = parser.parse_args()

    if args.convert:
        glove2word2vec(args.glove, args.model_path)

    elif args.query:
        print("Loading model")
        model = load_model(args.model_path)
        print("Model loaded")
        positive = []
        negative = []
        for term in args.terms:
            if term.startswith('-'):
                negative.append(term[1:])
            elif term.startswith('+'):
                positive.append(term[1:])
            else:
                positive.append(term)

        result = model.most_similar(positive=positive, negative=negative,
                topn=10)
        print(result)

