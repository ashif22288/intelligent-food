import pandas as pd
from pyjarowinkler import distance
import jellyfish


# Sample data for Table 1
data1 = {
    "Manufacturer": ["Apple", "Apple", "HP", "Apple", "Apple", "Acer", "Apple", "Apple", "Asus", "Acer", "HP", "HP", "Apple"],
    "Model Name": ["MBook Pro", "Macbook Air", "250 G6", "MacBook Pro", "MacBook Pro", "Aspire 3", "MacBook Pro", "Macbook Air",
                   "ZenBook UX430UN", "Swift 3", "250 G6", "250 G6", "MacBook Pro"],
    "Processor": ["M1", "M1", "Intel Core i3", "M1 Pro", "M1 Max", "Intel Core i5", "M2", "M1", 
                  "Intel Core i7", "AMD Ryzen 5", "Intel Core i3", "Intel Core i3", "M1"],
    "Screen Size": ["13.3", "13.3", "15.6", "14", "16", "15.6", "14", "13.3", "14", "14", "15.6", "15.6", "13.3"],
    "Display": ["Retina", "Retina", "HD", "Retina", "Retina", "Full HD", "Retina", "Retina", "Full HD", "Full HD", "HD", "HD", "Retina"],
    "Price": ["1,00,000 Rupees", "92,000 Rupees", "50,000 Rupees", "1,40,000 Rupees", "1,80,000 Rupees", 
              "65,000 Rupees", "1,10,000 Rupees", "95,000 Rupees", "80,000 Rupees", "70,000 Rupees", 
              "55,000 Rupees", "55,000 Rupees", "1,20,000 Rupees"],
    "Category": ["Ultrabook", "Ultrabook", "Notebook", "Ultrabook", "Ultrabook", "Notebook", "Ultrabook", "Ultrabook",
                 "Ultrabook", "Ultrabook", "Notebook", "Notebook", "Ultrabook"]
}

# Sample data for Table 2
data2 = {
    "idx": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    "name": [
        "Lenovo Intel Core i5 11th Gen", "Lenovo V15 G2 Core i3 11th Gen", "ASUS TUF Gaming F15 Core i5 10th Gen",
        "ASUS VivoBook 15 (2022) Core i3 10th Gen", "Lenovo Athlon Dual Core", "APPLE 2020 Macbook Air M1",
        "ASUS VivoBook 14 (2021) Celeron Dual Core", "DELL Vostro Ryzen 3 Quad Core 5425U",
        "Lenovo V15 G2 Core i3 11th Gen", "RedmiBook Pro Core i5 11th Gen"
    ],
    "Processor": [
        "Intel Core i5", "Intel Core i3", "Intel Core i5", "Intel Core i3", "Athlon Dual Core", "M1",
        "Celeron Dual Core", "Ryzen 3", "Intel Core i3", "Intel Core i5"
    ],
    "Screen Size": ["15.6", "15.6", "15.6", "15.6", "14", "13.3", "14", "14", "15.6", "15.6"],
    "Display": ["Full HD", "HD", "Full HD", "HD", "HD", "Retina", "HD", "Full HD", "HD", "Full HD"],
    "Price": ["1,300 Euros", "600 Euros", "700 Euros", "550 Euros", "500 Euros", 
              "1,000 Euros", "450 Euros", "800 Euros", "600 Euros", "750 Euros"]
}

# Exchange rate for conversion (example: 1 Euro = 88 Rupees)
EURO_TO_RUPEES = 88

# Function to convert prices to a common currency (Rupees)
def convert_to_rupees(price):
    price = price.replace(",", "")
    if "Rupees" in price:
        return int(price.split()[0])
    elif "Euros" in price:
        return int(price.split()[0]) * EURO_TO_RUPEES
    return 0

# Add converted prices
df1 = pd.DataFrame(data1)
df2 = pd.DataFrame(data2)

df1['Price (Rupees)'] = df1['Price'].apply(convert_to_rupees)
df2['Price (Rupees)'] = df2['Price'].apply(convert_to_rupees)

# Function for matching using pyjarowinkler (Jaro-Winkler and Jaro)
def match_column(value, df2_column):
    best_match = None
    best_score = float('-inf')
    
    for target in df2_column:
        # Calculate Levenshtein distance
        lev_distance = jellyfish.levenshtein_distance(value, target)
        # Calculate Jaro similarity (Jaro-Winkler is also based on Jaro)
        jaro_similarity = distance.get_jaro_distance(value, target)
        
        # Convert Levenshtein distance to a normalized score (lower distance = higher score)
        max_len = max(len(value), len(target))
        lev_score = (1 - lev_distance / max_len) * 100
        
        # Combine scores, giving more weight to Jaro similarity
        combined_score = 0.6 * jaro_similarity * 100 + 0.4 * lev_score
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = target
            
    return best_match, best_score

# Apply matching for Processor
df1['Best Processor Match'], df1['Processor Match Score'] = zip(
    *df1['Processor'].apply(lambda x: match_column(x, df2['Processor'].tolist()))
)

# Apply matching for Screen Size
df1['Best Screen Size Match'], df1['Screen Size Match Score'] = zip(
    *df1['Screen Size'].apply(lambda x: match_column(x, df2['Screen Size'].tolist()))
)

# Apply matching for Display
df1['Best Display Match'], df1['Display Match Score'] = zip(
    *df1['Display'].apply(lambda x: match_column(x, df2['Display'].tolist()))
)

# Apply matching for Price
df1['Best Price Match (Rupees)'], df1['Price Match Score'] = zip(
    *df1['Price (Rupees)'].apply(lambda x: match_column(str(x), df2['Price (Rupees)'].astype(str).tolist()))
)

# Filter matches with a score greater than 70%
filtered_df = df1[
    (df1['Processor Match Score'] > 70) |
    (df1['Screen Size Match Score'] > 70) |
    (df1['Display Match Score'] > 70) |
    (df1['Price Match Score'] > 70)
]

# Display the filtered results
print(filtered_df)
