from src.database import MySQLClient


class SchemaInspector:
    def __init__(self, conn):
        """
        Initialize the SchemaInspector with a database client.
        :param db_client: An instance of MySQLClient or similar.
        """
        self.conn: MySQLClient = conn

    def get_collection_info(self, collection_name=None):
        """
        Get information about a specific collection (table) or all collections in the database.
        :param collection_name: The name of the collection to get info about. If None, info about all collections is returned.
        :return: A dictionary containing schema information.
        """
        info = {}
        if collection_name:
            # Fetch info for a specific collection
            info[collection_name] = self._get_schema_details(collection_name)
        else:
            # Fetch info for all collections
            all_collections = self.conn.get_table_names()
            for coll in all_collections:
                info[coll] = self._get_schema_details(coll)
        return info

    def _get_schema_details(self, collection_name):
        """
        Helper method to fetch schema details for a given collection.
        :param collection_name: The name of the collection.
        :return: Schema details of the collection.
        """
        query = f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{collection_name}' AND TABLE_SCHEMA = '{self.conn.db}'"
        return self.conn.execute(query)
