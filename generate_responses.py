import google.generativeai as genai
from groq import Groq
import pandas as pd
import sys
import os
import time
from pathlib import Path


def setup_models():
    # Setup Gemini
    gemini_key = open("gemini_api_key.txt").read().strip()
    genai.configure(api_key=gemini_key)
    gemini_model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config=genai.GenerationConfig(temperature=0.0)
    )
    
    # Setup Groq
    groq_key = open("groq_api_key.txt").read().strip()
    groq_client = Groq(api_key=groq_key)
    groq_model = "llama-3.1-8b-instant" # using instant model, intending different responses
    
    return gemini_model, groq_client, groq_model


def ask_gemini(model, prompt):
    """Send prompt to Gemini and return response."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


def ask_groq(client, model, prompt):
    """Send prompt to Groq and return response."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def process_csv(input_file, output_file):
    """
    Process CSV file with prompts and add response columns. columns: index, prompt, etc.
    """
    print("Started generating responses. This may take a while.")
    
    # Read CSV file
    df = pd.read_csv(input_file)
    
    # Verify required columns
    if 'prompt' not in df.columns:
        raise ValueError("CSV file must contain 'prompt' column")
    
    # Setup models
    gemini_model, groq_client, groq_model = setup_models()
    
    # Add response columns if they don't exist
    if 'gemini_response' not in df.columns:
        df['gemini_response'] = ''
    if 'groq_response' not in df.columns:
        df['groq_response'] = ''
    
    # Process each prompt
    total = len(df)
    for idx, row in df.iterrows():
        prompt = row['prompt']
        
        # Get Gemini response
        df.at[idx, 'gemini_response'] = ask_gemini(gemini_model, prompt)
        time.sleep(1)  # Delay to avoid rate limiting
        
        # Get Groq response
        df.at[idx, 'groq_response'] = ask_groq(groq_client, groq_model, prompt)
        time.sleep(1)  # Delay to avoid rate limiting
    
    # Save results
    df.to_csv(output_file, index=False)
    print("csv file with generated prompts saved.")
    
    return df


def main():
    """Main function to process CSV files."""
    if len(sys.argv) < 2:
        print("Usage: python generate_responses.py <input_csv> [output_csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Generate output filename if not provided
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Create output filename by adding _responses before .csv
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_responses{input_path.suffix}"
    
    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Process the CSV
    process_csv(input_file, output_file)


if __name__ == "__main__":
    main()
