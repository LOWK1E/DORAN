try:
    from sentence_transformers import SentenceTransformer, util
    sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    sentence_model = None

def semantic_similarity(query, corpus):
    """
    Compute semantic similarity between query and a list of corpus sentences.
    Returns the most similar sentence and similarity score.
    If sentence_transformers is not available, returns None.
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE or sentence_model is None:
        return None, 0.0
    
    query_emb = sentence_model.encode(query, convert_to_tensor=True)
    corpus_emb = sentence_model.encode(corpus, convert_to_tensor=True)
    hits = util.semantic_search(query_emb, corpus_emb, top_k=1)
    if hits and hits[0]:
        top_hit = hits[0][0]
        return corpus[top_hit['corpus_id']], top_hit['score']
    return None, 0.0
