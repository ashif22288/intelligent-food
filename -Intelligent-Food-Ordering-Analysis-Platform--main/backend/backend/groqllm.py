import os
from groq import Groq
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
def generate_intelligent_query(prompt):
    model = genai.GenerativeModel('gemini-pro')
    #robustly convert the response from string to json
    response = model.generate_content(prompt)
    return response.text
# Function to generate intelligent database query
# def generate_intelligent_query(prompt):
    
#     chat_completion = client.chat.completions.create(
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         model="mixtral-8x7b-32768"  # Mixtral model for complex reasoning
#     )
    
#     return chat_completion.choices[0].message.content

# # Example usage
# database_context = """
# Tables:
# - users (id, name, email, registration_date)
# - orders (id, user_id, product_id, order_date, total_amount)
# - products (id, name, category, price)
# """

# query_goal = "Find top 5 customers by total spending in the last 3 months"

# intelligent_query = generate_intelligent_query(database_context, query_goal)
# print("Recommended SQL Query:")
# print(intelligent_query)