import re
import pymysql


class DatabaseClient:
    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password = password
        self.db = db

    def insert(self, collection_name, data):
        # Implementation for the CREATE operation
        pass

    def read(self, collection_name, conditions={}):
        # Implementation for the READ operation
        pass

    def update(self, collection_name, data, conditions={}):
        # Implementation for the UPDATE operation
        pass

    def delete(self, collection_name, conditions={}):
        # Implementation for the DELETE operation
        pass

    def execute(self, data=None):
        # Implementation for the DELETE operation
        pass


class MySQLClient(DatabaseClient):
    def __init__(self, host, user, password, db):
        super().__init__(host, user, password, db)
        self.query = ""
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.db)

    def _build_conditions(self, conditions={}):
        """ Helper method to build the WHERE clause from a dictionary of conditions. """
        if not conditions:
            return ""
        C = []
        for key, value in conditions.items():
            if not re.fullmatch(r'%\(\w+\)s', value):
                value = f"'{value}'"
            C.append(f"{key}={value}")
        return " WHERE " + " AND ".join(C)

    def _build_columns(self, data):
        keys = [entry.keys() for entry in data]
        keys = set().union(*keys)
        return keys
    
    def insert(self, collection_name, data, ignore=False, **kwargs):
        if not data:
            return None
        if isinstance(data, dict):
            data = [data]
        # Assuming 'data' is a dictionary representing columns and their values
        keys = self._build_columns(data)
        columns = ', '.join(keys)
        placeholders = ', '.join([f"%({k})s" for k in keys])
        instruction = "INSERT IGNORE" if ignore else "INSERT"
        self.query = f"{instruction} INTO {collection_name} ({columns}) VALUES ({placeholders})"
        return self.execute(data=data, **kwargs)
        # Execute the query or return it

    def read(self, collection_name, conditions={}):
        condition_string = self._build_conditions(conditions)
        self.query = f"SELECT * FROM {collection_name}{condition_string}"
        return self.execute()

    def update(self, collection_name, data, conditions={}, ignore=False, **kwargs):
        if not data:
            return None
        if isinstance(data, dict):
            data = [data]
        keys = self._build_columns(data)
        update_string = ', '.join([f"{key}=%({key})s" for key in keys])
        condition_string = self._build_conditions(conditions)
        instruction = "UPDATE IGNORE" if ignore else "UPDATE"
        self.query = f"{instruction} {collection_name} SET {update_string}{condition_string}"
        return self.execute(data=data, **kwargs)
        # Execute the query or return it

    def delete(self, collection_name, conditions={}):
        condition_string = self._build_conditions(conditions)
        self.query = f"DELETE FROM {collection_name}{condition_string}"
        return self.execute()
        # Execute the query or return it

    def get_table_names(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            return [e for e, *_ in cursor.fetchall()]

    def execute(self, query=None, data=None, **kwargs):
        """
        Executes a given SQL query or the query stored in self.query.

        Args:
            query (str, optional): The SQL query or script to execute. Defaults to None.

        Returns:
            list[dict]: List of dictionaries containing query results for SELECT queries.
        """
        if query is None:
            query = self.query

        # Split the query into individual statements if it's a script
        queries = re.split(';', query)
        
        results = []
        for q in queries:
            q = q.strip()
            if q:
                with self.conn.cursor() as cursor:
                    if data:
                        for i in range(len(data)):
                            data[i].update(kwargs)

                        cursor.executemany(q, data)
                    else:
                        cursor.execute(q)
                    return_results = q.upper().startswith("SELECT")
                    if return_results:
                        # Fetch results for SELECT queries
                        heads = [e[0] for e in cursor.description]
                        data = [dict(zip(heads, e)) for e in cursor.fetchall()]
                        results.extend(data)

                    # Commit after each non-SELECT query
                    else:
                        self.conn.commit()

        return results


    def load_sql_from_file(self, file_path, **kwargs):
        """
        Loads a SQL script from the specified file and formats it with the provided kwargs.

        Args:
            file_path (str): Path to the SQL file.
            **kwargs: Keyword arguments for formatting the SQL script.

        Returns:
            str: The formatted SQL script.
        """
        try:
            # Read the SQL script from the file
            with open(file_path, 'r') as file:
                script = file.read()

            # Format the script using the provided keyword arguments
            formatted_script = script.format(**kwargs)

            self.query = formatted_script
        except IOError as e:
            # Handle file reading errors
            print(f"Error reading file {file_path}: {e}")
            return None
        except KeyError as e:
            # Handle formatting errors (e.g., missing keys in kwargs)
            print(f"Error formatting the SQL script: Missing key {e}")
            return None

