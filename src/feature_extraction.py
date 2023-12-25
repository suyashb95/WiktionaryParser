from collections import Counter


class FeatureExtractor:
    def __init__(self, conn, 
                 embedding_type="category_embedding",
                 word_table="words", 
                 dataset_table="data", 
                 edge_table="relationships",
                 definitions_table="definitions",
                ):

        self.conn = conn
        self.embedding_type = embedding_type
        self.word_table = word_table
        self.dataset_table = dataset_table
        self.definitions_table = definitions_table
        self.edge_table = edge_table

    def __get_category_embedding(self, token_id):
        # Define the fields and join conditions for the query
        fields = "c.text"
        # fields = "*"
        joins = [("word_categories wc", f"wc.categoryId = c.id")]
        conditions = {"wc.wordId": token_id}

        # Execute the query using the read method of DatabaseClient
        result = self.conn.read(collection_name="categories c", fields=fields, joins=joins, conditions=conditions)
        print(self.conn.query)
        # Processing the result into a dictionary
        categories = dict(Counter([row['text'] for row in result]))

        return categories
    
    def __call__(self, token_id):
        if self.embedding_type == 'category_embedding':
            embeds = self.__get_category_embedding(token_id)
            return embeds
        else:
            return []
        

    