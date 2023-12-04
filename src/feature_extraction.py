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
        query = f"""SELECT c.text,
            CASE 
            WHEN EXISTS (
                SELECT * FROM word_categories wc
                WHERE wc.wordId = '{token_id}'
                AND wc.categoryId = c.id
            )
            THEN 1
            ELSE 0
            END enc
            FROM categories c
            ORDER BY c.id;
        """
        cur = self.conn.cursor()
        result = cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in cur.fetchall()]

        categories = {}
        for r in result:
            categories[r.get('text')] = r.get('enc')

        return categories
    
    def __call__(self, token_id):
        if self.embedding_type == 'category_embedding':
            embeds = self.__get_category_embedding(token_id)
            return [embeds[k] for k in sorted(embeds)]
        else:
            return []
        

    