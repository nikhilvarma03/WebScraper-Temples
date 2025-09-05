import pandas as pd
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from tqdm import tqdm
import os

# ========== CONFIG ==========
INPUT_FILE = "tamil_nadu_temples_with_locations.xlsx"
OUTPUT_FILE = "tamil_nadu_temples_with_locations_standardized.xlsx"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-3.5-turbo"
MAX_TOKENS = 12
TEMPERATURE = 0

# ========== SETUP ==========
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS
)

# System prompt for strict city/town/village extraction
system_prompt = SystemMessage(
    content=(
        "You are a helpful assistant that extracts ONLY the city, town, "
        "or village name from a given location string. "
        "Do not include the state name, punctuation, or explanations. "
        "If you cannot determine a town/city/village, reply exactly: UNKNOWN"
    )
)

# Template for user prompt


def build_user_prompt(location_str):
    return HumanMessage(content=f"Input location: \"{location_str}\"")

# Heuristic preprocessing to strip obvious state names, etc.


def preprocess_location(loc):
    if pd.isna(loc):
        return ""
    loc = str(loc).strip()
    # Remove Tamil Nadu or similar state names
    loc = re.sub(r"\bTamil Nadu\b", "", loc, flags=re.IGNORECASE)
    # Remove common Indian state names (extend if needed)
    states = [
        "Andhra Pradesh", "Kerala", "Karnataka", "Telangana", "Puducherry",
        "Maharashtra", "Odisha", "Bihar", "West Bengal"
    ]
    for state in states:
        loc = re.sub(rf"\b{state}\b", "", loc, flags=re.IGNORECASE)
    # Remove extra commas, spaces
    loc = re.sub(r"\s*,\s*", ",", loc)
    loc = loc.strip(", ")
    return loc


# Load Excel
df = pd.read_excel(INPUT_FILE)
df.columns = df.columns.str.lower()

if "location" not in df.columns:
    raise ValueError("Input file must have a 'location' column.")

# Preprocess
df["preprocessed_location"] = df["location"].apply(preprocess_location)

# Deduplicate unique inputs
unique_locations = df["preprocessed_location"].dropna().unique()

# Dictionary to store mappings
location_map = {}

# Call LLM only for unique values
print(f"Processing {len(unique_locations)} unique locations via LLM...")
for loc in tqdm(unique_locations):
    if not loc.strip():
        location_map[loc] = "UNKNOWN"
        continue
    # LLM call
    messages = [system_prompt, build_user_prompt(loc)]
    try:
        response = llm.invoke(messages)
        standardized = response.content.strip()
    except Exception as e:
        print(f"Error for '{loc}': {e}")
        standardized = "UNKNOWN"
    location_map[loc] = standardized

# Map back to DataFrame
df["standard_location"] = df["preprocessed_location"].map(location_map)

# Save to new Excel
df.to_excel(OUTPUT_FILE, index=False)
print(f"✅ Standardized file saved to: {OUTPUT_FILE}")
