import mysql.connector
import json
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Token
from sqlparse.tokens import Keyword, DML


# Database connection to global schema
global_conn = mysql.connector.connect(
    host="localhost",
    user="sqluser",
    password="password",
    database="global_schema",
    auth_plugin='mysql_native_password'
)

def global_query_results(query):
    try:
        global_conn.ping(reconnect=True)
        global_cursor = global_conn.cursor()
        global_cursor.execute(query)
        results = global_cursor.fetchall()
        global_cursor.close()
        return results
    except mysql.connector.Error as err:
        print(f"Error executing global query: {err}")
        print(f"Query that failed: {query}")
        return None

def vendor_query_results(transformed_query, details):
    try:
        vendor_conn = mysql.connector.connect(
            host=details['database_info']['ip'],
            user=details['database_info']['user'],
            password=details['database_info']['password'],
            database=details['database_info']['db_name'],
            auth_plugin='mysql_native_password'
        )
        vendor_cursor = vendor_conn.cursor()
        vendor_cursor.execute(transformed_query)
        results = vendor_cursor.fetchall()
        vendor_cursor.close()
        vendor_conn.close()
        return results
    except mysql.connector.Error as err:
        print(f"Error executing vendor query: {err}")
        print(f"Query that failed: {transformed_query}")
        return None

def transform_sql_query(global_query, schema_mappings):
    """
    Transforms a global schema SQL query into a vendor-specific query using mappings,
    excluding columns mapped to null.
    
    Args:
        global_query (str): The query in the global schema.
        schema_mappings (dict): Mappings that include table and column mappings.
    
    Returns:
        str: Transformed query for the vendor schema.
    """
    import re

    # Extract mappings
    database_mapping = schema_mappings.get("database_mapping_global_schema", {})
    table_mappings = database_mapping.get("table_mappings", {})
    column_mappings = database_mapping.get("column_mappings", {})

    def replace_table_and_columns(match):
        """
        Replaces table and column names in the SQL query.
        If a column maps to null, it is removed from the query.
        
        Args:
            match (re.Match): The regex match object.
        
        Returns:
            str: Transformed table.column or column, or an empty string for null mappings.
        """
        full_identifier = match.group(0)  # Full match
        table = match.group(1)  # Table or alias (optional)
        column = match.group(2)  # Column name

        # Transform table and column using mappings
        actual_table = table_mappings.get(table, table) if table else None
        actual_column = (
            column_mappings.get(table, {}).get(column, column) if table else column
        )

        if actual_column is None:
            # Exclude columns mapped to null
            return ""

        if actual_table:
            return f"`{actual_table}`.`{actual_column}`"
        return f"`{actual_column}`"

    # Regex for identifying `table`.`column` or `column`
    regex = r"`?([a-zA-Z_][a-zA-Z0-9_]*)`?\.`?([a-zA-Z_][a-zA-Z0-9_]*)`?"

    # Replace table and column names in the query
    transformed_query = re.sub(regex, replace_table_and_columns, global_query)

    # Remove any dangling commas or invalid syntax
    transformed_query = re.sub(r",\s*,", ", ", transformed_query)  # Remove extra commas
    transformed_query = re.sub(r"\s*,\s*$", "", transformed_query)  # Remove trailing comma

    return transformed_query


def fed_query(global_query):
    # Clean up the query
    global_query = ' '.join(global_query.split()).replace(' ,', ',')
    #print(f"Executing global query: {global_query}")
    
    # Step 1: Execute the global query
    global_results = global_query_results(global_query)
    # print("Global Results:", global_results)
    final_results = []
    final_results.append(global_results)
    
    
    if global_results:
        #try:
            # Load the schema_mappings.json file
            with open('schema_mappings.json') as f:
                schema_mappings = json.load(f)
                
                # Process each vendor schema
                for vendor_name, mapping in schema_mappings.items():
                    other_relevant_details = {
                        'database_info': mapping['database_info']
                        
                    }
                    
                    transformed_query = transform_sql_query(
                        global_query, 
                        mapping
                    )
                    
                    print(f"Transformed query for {vendor_name}:", transformed_query)
                    
                    # Execute the transformed query
                    vendor_results = vendor_query_results(transformed_query, mapping)
                    if vendor_results:
                        final_results.append(vendor_results)
            
            return final_results if final_results else None
            
    else:
        return None

def final_query_result(query):
    result = fed_query(query)
    print("Final Results:", result)
    return result


# Example Execution
if __name__ == "__main__":
    sample_query = """
        SELECT `Restaurant`.`Name`, `Dishes`.`Dishname`, `Dishes`.`price` 
        FROM `Restaurant` 
        JOIN `Dishes` ON `Restaurant`.`Restaurant_id` = `Dishes`.`restaurant_id` 
        WHERE `Restaurant`.`City` = 'New York' AND `Dishes`.`availability` = 1;
    """
    results = fed_query(sample_query)
    print("Final Results:", results)