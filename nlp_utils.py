import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

def preprocess_text(text):
    """Preprocess text by tokenizing, removing stopwords and punctuation."""
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and word not in string.punctuation]
    return ' '.join(tokens)

def semantic_similarity(query, corpus):
    """
    Compute similarity between query and a list of corpus sentences using TF-IDF and cosine similarity.
    Returns the most similar sentence and similarity score.
    """
    if not corpus:
        return None, 0.0
    
    # Preprocess query and corpus
    processed_query = preprocess_text(query)
    processed_corpus = [preprocess_text(doc) for doc in corpus]
    
    # Add query to corpus for vectorization
    all_texts = [processed_query] + processed_corpus
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Compute cosine similarity between query and corpus
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Find the most similar document
    if len(cosine_similarities) > 0:
        max_idx = cosine_similarities.argmax()
        max_score = cosine_similarities[max_idx]
        return corpus[max_idx], float(max_score)
    
    return None, 0.0
