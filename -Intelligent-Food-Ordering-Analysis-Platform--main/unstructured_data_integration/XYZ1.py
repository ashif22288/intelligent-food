import jellyfish
import pandas as pd
from pyjarowinkler import distance
import pymysql

# SQL Connection Information
connection_config = {
    'host': 'localhost',
    'user': 'sqluser',
    'password': 'password',
    'database': 'new_restaurant_schema',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Exchange rate for conversion (example: 1 Euro = 88 Rupees)
EURO_TO_RUPEES = 88

# Function to convert prices to a common currency (Rupees)
def convert_to_rupees(price):
    price = price.replace(",", "")
    if "rupees" in price.lower():
        return int(price.split()[0])  # If already in rupees
    elif "euros" in price.lower():
        return int(price.split()[0]) * EURO_TO_RUPEES  # Convert Euros to Rupees
    return 0

# Function to calculate similarity using Jaro-Winkler distance
def calculate_similarity(input_name, target_name):
    return distance.get_jaro_distance(input_name, target_name, winkler=True, scaling=0.1)

# Function to find the best match for the input laptop name
def find_laptop_by_name(input_name, excel_df, sql_df, similarity_threshold=0.7):
    matches = []

    # Normalize the input name
    input_name = input_name.strip().lower()

    # Search in Excel-like dataset
    for _, row in excel_df.iterrows():
        model_name = row.get("model name", "").strip().lower()
        if model_name:
            similarity_score = calculate_similarity(input_name, model_name)
            if similarity_score >= similarity_threshold:
                matches.append(("Excel", row.to_dict(), similarity_score))

    # Search in SQL-like dataset
    for _, row in sql_df.iterrows():
        name = row.get("name", "").strip().lower()
        if name:
            similarity_score = calculate_similarity(input_name, name)
            if similarity_score >= similarity_threshold:
                matches.append(("SQL", row.to_dict(), similarity_score))

    # Sort matches by similarity score in descending order
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches

# Fetch data from SQL database
def fetch_sql_data():
    try:
        connection = pymysql.connect(**connection_config)
        query = "SELECT `idx`, `name`, `price(in Rs.)` AS price, `processor`, `display(in inch)` AS `screen size`, `rating` AS `display` FROM `database1`"
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching data from SQL: {e}")
        return pd.DataFrame()
    finally:
        connection.close()

# Main function
def main():
    # Read the Excel-like dataset from a CSV file
    try:
        df_excel = pd.read_csv(r"C:\Users\WASIF\Downloads\laptops.csv", encoding='latin1', engine='python')
    except FileNotFoundError:
        print("Error: The file 'laptop.csv' was not found. Please provide the correct file path.")
        return
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # Normalize column names
    df_excel.columns = df_excel.columns.str.strip().str.lower()

    # Ensure 'price (euros)' column exists
    if 'price (euros)' not in df_excel.columns:
        print("Error: 'price (euros)' column not found.")
        return

    # Convert Price (Euros) to Rupees
    df_excel['price (rupees)'] = df_excel['price (euros)'].apply(convert_to_rupees)

    # Fetch data from SQL database
    df_sql = fetch_sql_data()

    # Normalize column names in SQL DataFrame
    df_sql.columns = df_sql.columns.str.strip().str.lower()

    # Convert Price to Rupees (assuming the SQL data also uses 'price' as column)
    df_sql['price (rupees)'] = df_sql['price'].astype(int)

    # Get user input for laptop name
    input_name = input("Enter the name of the laptop to search: ").strip()

    # Find matches
    matching_laptops = find_laptop_by_name(input_name, df_excel, df_sql)

    # Display results
    if matching_laptops:
        print(f"\nFound {len(matching_laptops)} matching laptops:\n")
        for source, laptop, score in matching_laptops:
            print(f"Source: {source} (Similarity Score: {score:.2f})")
            for key, value in laptop.items():
                print(f"{key}: {value}")
            print("-" * 50)
    else:
        print("\nNo matching laptops found.")

if __name__ == "__main__":
    main()
