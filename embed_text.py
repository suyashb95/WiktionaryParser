

from src.feature_extraction import FeatureExtractor
from scripts.utils import conn

fe = FeatureExtractor(conn=conn, embedding_type="llm_embedding")
print(fe('1596c68b103543e3c3bfee450d31588bf3448c5ed8dca4ae8b7b546747ada872'))