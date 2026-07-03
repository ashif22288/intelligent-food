import pymysql
from transformers import pipeline
import re

# Initialize the GPT-Neo model for text generation/parsing
generator = pipeline("text-generation", model="EleutherAI/gpt-neo-1.3B", framework="pt", truncation=True)

# Connect to MySQL database
connection = pymysql.connect(
    host='localhost',
    user='aditya',
    password='12345678',
    database='global_schema',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


# Function to insert data into Restaurant table
def insert_restaurant(cursor, name, address, city, zip_code, rating, availability):
    if not zip_code:  # Handle missing or invalid ZIP code
        zip_code = '00000'  # Default to a placeholder if necessary
    
    query = """
    INSERT INTO Restaurant (Name, Address, City, Zip, Rating, availability)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, address, city, zip_code, rating, availability))
    return cursor.lastrowid  # Return the ID of the inserted restaurant


# Function to insert data into Dishes table
def insert_dish(cursor, dishname, price, restaurant_id, rating, availability):
    query = """
    INSERT INTO Dishes (Dishname, price, restaurant_id, rating, availability)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (dishname, price, restaurant_id, rating, availability))

# Use the LLM model to extract information from the unstructured input
def extract_with_llm(document_content):
    prompt = f"Extract structured data from the following text, including restaurant name, address, city, zip code, rating, and all the  dishes with their prices and ratings:\n\n{document_content}\n\nOutput the data in this format: Restaurant Name, Address, City, Zip Code, Rating, [Dish Name (Price, Rating), ...]"
    
    # Generate a structured response using the LLM
    output = generator(prompt, max_length=300, do_sample=True)[0]['generated_text']
    
    return output

# Function to parse the LLM output and structure it
def parse_llm_output(llm_output):
    print("LLM Output:\n", llm_output)

    # Define regular expressions to extract the required information
    restaurant_name_match = re.search(r"establishment,\s*(.+?),", llm_output)
    address_match = re.search(r"Located at\s*(.+?),", llm_output)
    city_match = re.search(r"in\s*(.+?),\s*with a zip code", llm_output)
    zip_code_match = re.search(r"zip code of\s*(\d+)", llm_output)
    rating_match = re.search(r"boasts a rating of\s*([\d.]+)", llm_output)

    # Extract restaurant information with fallback handling
    restaurant_info = {
        'name': restaurant_name_match.group(1) if restaurant_name_match else None,
        'address': address_match.group(1) if address_match else None,
        'city': city_match.group(1) if city_match else None,
        'zip': None,  # Default value
        'rating': float(rating_match.group(1)) if rating_match else None,
        'dishes': []
    }

    # Debugging: Print parsed restaurant info
    print(f"Parsed Restaurant Info: {restaurant_info}")

    # Check if zip code is valid
    if zip_code_match:
        zip_code = zip_code_match.group(1).strip()
        if zip_code.isdigit() and len(zip_code) == 5:  # Example check for 5-digit zip codes
            restaurant_info['zip'] = zip_code
        else:
            print(f"Invalid ZIP code: {zip_code}")
            restaurant_info['zip'] = None  # Handle invalid ZIP gracefully

    # Extract dish information
    dish_matches = re.findall(r"including\s*(.+?)\s+priced at\s*\$(\d+)\s+with a rating of\s*([\d.]+)", llm_output)

    for dish in dish_matches:
        dish_info = {
            'dishname': dish[0].strip(),
            'price': int(dish[1].strip()),
            'rating': float(dish[2].strip())
        }
        restaurant_info['dishes'].append(dish_info)

    return restaurant_info

# Process the data and insert it into the database
def process_and_report_with_llm(document_content):
    llm_output = extract_with_llm(document_content)
    data = parse_llm_output(llm_output)
    report = {}

    try:
        with connection.cursor() as cursor:
            # Insert restaurant and get the ID
            restaurant_id = insert_restaurant(cursor, data['name'], data['address'], data['city'],
                                              data['zip'], data['rating'], True)
            report['restaurant'] = data['name']

            # Insert dishes and prepare report
            report['dishes'] = []
            for dish in data['dishes']:
                insert_dish(cursor, dish['dishname'], dish['price'], restaurant_id, dish['rating'], True)
                report['dishes'].append(f"{dish['dishname']} (Price: ${dish['price']}, Rating: {dish['rating']})")
            
            connection.commit()

    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()

    finally:
        connection.close()

    return report

# Example of processing a document and reporting the result
document_content = """As a restaurant owner eager to add my establishment, The Spice House, the platform, I am excited to provide detailed information about my restaurant and its dishes. Located at 456 Flavor St, New Delhi, with a zip code of 67890, The Spice House boasts a rating of 4.5 and is fully available for patrons. I offer a variety of delicious dishes, including Spicy Curry priced at $15 with a rating of 4.7, Grilled Salmon at $20 with a rating of 4.9, and a Vegan Buddha Bowl for $12 with a rating of 4.8.  
Thanks 
-mukesh"""

# Run the process and print the added information
report = process_and_report_with_llm(document_content)

print(f"Added Restaurant: {report['restaurant']}")
for dish in report['dishes']:
    print(f"Added Dish: {dish}")
