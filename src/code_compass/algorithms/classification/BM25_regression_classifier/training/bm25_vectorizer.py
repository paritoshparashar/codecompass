import numpy as np
from scipy.sparse import csr_matrix  # noqa: F401
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer


class BM25Vectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, k1=1.5, b=0.75, max_features=10000, min_df=2):
        self.k1 = k1
        self.b = b
        self.max_features = max_features
        self.min_df = min_df

        self.count_vectorizer = CountVectorizer(
            max_features=self.max_features, min_df=self.min_df, ngram_range=(1, 1)
        )

    def fit(self, X, y=None):

        # Build vocabulary and obtain term frequencies
        X_counts = self.count_vectorizer.fit_transform(X)

        # Number of training documents
        self.n_docs_ = X_counts.shape[0]

        # Document frequency: number of documents containing each term
        document_frequency = np.asarray((X_counts > 0).sum(axis=0)).ravel() # type: ignore

        # Calculate IDF
        self.idf_ = np.log(
            1 + (self.n_docs_ - document_frequency + 0.5) / (document_frequency + 0.5)
        )

        # Calculate document lengths
        document_lengths = np.asarray(X_counts.sum(axis=1)).ravel() # type: ignore

        # Calculate average document length
        self.avgdl_ = document_lengths.mean()

        return self

    def transform(self, X):

        # Convert incoming text into term-frequency vectors
        X_counts = self.count_vectorizer.transform(X)
        X_counts = X_counts.tocsr().astype(float) # type: ignore

        # Calculate lengths of incoming documents
        document_lengths = np.asarray(X_counts.sum(axis=1)).ravel()

        # Identify which document each non-zero term belongs to
        rows = np.repeat(np.arange(X_counts.shape[0]), np.diff(X_counts.indptr))

        # Term frequencies
        tf = X_counts.data

        # Document length normalization
        if self.avgdl_ > 0:
            length_norm = 1 - self.b + self.b * document_lengths[rows] / self.avgdl_
        else:
            length_norm = np.ones_like(tf)

        # Calculate BM25 weights
        denominator = tf + self.k1 * length_norm

        X_counts.data = self.idf_[X_counts.indices] * (tf * (self.k1 + 1)) / denominator

        return X_counts
