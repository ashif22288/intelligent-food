import json
import google.generativeai as genai
import pymysql
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re


#don't you dare to misuse my api key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='sqluser',
        password='password',
        database='global_schema',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def check_if_dish_exists(restaurant_name, city):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id FROM restaurant WHERE Name = %s AND City = %s"
            cursor.execute(sql, (restaurant_name, city))
            result = cursor.fetchone()
            if result:
                return result['id']  # Return the restaurant ID if found
            else:
                return None
    finally:
        connection.close()

# Check if a dish already exists based on the restaurant_id and dish name
def check_dish(restaurant_id, name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id FROM dishes WHERE restaurant_id = %s AND Dishname = %s"
            cursor.execute(sql, (restaurant_id, name))
            result = cursor.fetchone()
            if result:
                return True  # Dish already exists
            else:
                return False
    finally:
        connection.close()

# Insert new restaurant data
def insert_into_restaurant(name, address, city, zip_code, rating, availability):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO restaurant (Name, Address, City, Zip, Rating, availability)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (name, address, city, zip_code, rating, availability))
            connection.commit()
            return cursor.lastrowid  # Return the restaurant ID of the inserted row
    finally:
        connection.close()

# Insert new dish data
def insert_into_dishes(restaurant_id, name, price, rating):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO dishes (Dishname, price, restaurant_id, rating)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (name, price, restaurant_id, rating))
            connection.commit()
            return cursor.lastrowid  # Return the dish ID of the inserted row
    finally:
        connection.close()


    
def get_text_from_file(file_path):
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.txt':
        with open(file_path, 'r') as file:
            return file.read()
    elif file_extension.lower() == '.pdf':
        pages = convert_from_path(file_path, 500)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page)
        return text
    elif file_extension.lower() in ['.png', '.jpg', '.jpeg']:
        return pytesseract.image_to_string(Image.open(file_path))
    else:
        raise ValueError("Unsupported file type")

def process_input_file():
    file_path = input("Enter the path to the input file (txt, pdf, or image): ")
    text = get_text_from_file(file_path)
    
    model = genai.GenerativeModel('gemini-pro')
    prompt = """
    Find the structured data from the following document:
    - Restaurant details (name, address, city, zip code, rating, availability)
    - Dishes with prices and ratings
    
    Provide the extracted data in a structured text format like below:
    Expected format:
    {
      "Restaurant": {
        "name": "The Spice House",
        "address": "456 Flavor St",
        "city": "New Delhi",
        "zip": "67890",
        "rating": 4.5,
        "availability": 1
      },
      "Dish": [
        {
          "name": "dish name1",
          "price": 15.00,
          "rating": 4.7
        },
        {
          "name": "dish name",
          "price": 20.00,
          "rating": 4.9
        }
      ]
    }
    """
    prompt += text
    
    response = model.generate_content(prompt)
    print(response.text)
    structured_data = parse_response(response.text)
    
    if structured_data:
        restaurant_id = insert_restaurant_data(structured_data['restaurant'])
        insert_dish_data(restaurant_id, structured_data['dishes'])
        print("Data successfully inserted into the database.")
    else:
        print("Failed to parse and insert data.")

def parse_response(response_text):
    
    try:
        # Cleaning up and extracting potential JSON content
        # Remove any extraneous whitespace
        response_text = response_text.strip()

        # Attempt to load directly if response is proper JSON format
        try:
            structured_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Attempt to clean up and fix common JSON issues, like single quotes or trailing commas
            response_text = response_text.replace("'", '"')  # Replace single quotes with double quotes for JSON
            response_text = re.sub(r',\s*}', '}', response_text)  # Remove trailing commas before closing brace
            response_text = re.sub(r',\s*]', ']', response_text)  # Remove trailing commas before closing square bracket
            
            # Attempt to parse the cleaned-up text
            structured_data = json.loads(response_text)

        # Validate presence of restaurant and dish information
        if 'Restaurant' not in structured_data or 'Dish' not in structured_data:
            raise ValueError("Required 'Restaurant' or 'Dish' key missing from structured data")

        # Extract restaurant details
        restaurant_data = structured_data['Restaurant']
        restaurant = {
            'name': restaurant_data.get('name', ''),
            'address': restaurant_data.get('address', ''),
            'city': restaurant_data.get('city', ''),
            'zip': restaurant_data.get('zip', ''),
            'rating': float(restaurant_data.get('rating', 0.0)),
            'availability': int(restaurant_data.get('availability', 0))
        }

        # Extract dish details
        dishes = []
        for dish in structured_data['Dish']:
            dishes.append({
                'name': dish.get('name', ''),
                'price': float(re.sub(r'[^\d.]', '', str(dish.get('price', 0.0)))),
                'rating': float(dish.get('rating', 0.0))
            })

        # Prepare the return value
        parsed_data = {
            'restaurant': restaurant,
            'dishes': dishes
        }

        # Print the return value (for debugging purposes)
        print("Parsed Response:")
        print(json.dumps(parsed_data, indent=2))

        # Return structured data
        return parsed_data

    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing the response: {e}")
        return None

def insert_restaurant_data(restaurant_data):
    restaurant_id = insert_into_restaurant(
        restaurant_data['name'],
        restaurant_data['address'],
        restaurant_data['city'],
        restaurant_data['zip'],
        restaurant_data['rating'],
        restaurant_data['availability']
    )
    print(restaurant_data['name'],
        restaurant_data['address'],
        restaurant_data['city'],
        restaurant_data['zip'],
        restaurant_data['rating'],
        restaurant_data['availability'])
    return restaurant_id

def insert_dish_data(restaurant_id, dishes):
    for dish in dishes:
        print( restaurant_id,
            dish['name'],
            dish['price'],
            dish['rating'])
        insert_into_dishes(
            restaurant_id,
            dish['name'],
            dish['price'],
            dish['rating']
        )

if __name__ == "__main__":
    process_input_file()
