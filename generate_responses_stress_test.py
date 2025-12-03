import google.generativeai as genai
from groq import Groq
import pandas as pd
import os
import time
from pathlib import Path


def setup_models():
    gemini_key = open("gemini_api_key.txt").read().strip()
    genai.configure(api_key=gemini_key)
    gemini_model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config=genai.GenerationConfig(temperature=0.0)
    )

    groq_key = open("groq_api_key.txt").read().strip()
    groq_client = Groq(api_key=groq_key)
    groq_model_name = "llama-3.1-8b-instant"

    return gemini_model, groq_client, groq_model_name


def ask_gemini(model, prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini Error: {str(e)}"


def ask_groq(client, model_name, prompt):
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq Error: {str(e)}"


def run_stress_tests(input_csv_path):
    input_path = Path(input_csv_path)

    output_csv = input_path.parent / f"{input_path.stem}_responses.csv"

    print(f"Loading prompts from: {input_path}")
    df = pd.read_csv(input_path)

    if "prompt" not in df.columns:
        raise ValueError("CSV must contain a 'prompt' column.")

    if "index" not in df.columns:
        df["index"] = range(1, len(df) + 1)

    gemini_model, groq_client, groq_model = setup_models()

    if "gemini_response" not in df.columns:
        df["gemini_response"] = ""
    if "groq_response" not in df.columns:
        df["groq_response"] = ""

    total = len(df)
    print(f"Running stress tests for {total} prompts")

    for i, (idx, row) in enumerate(df.iterrows(), start=1):
        prompt = row["prompt"]
        print(f"{i}/{total}: {row['index']}")

        if not row.get("gemini_response"):
            df.at[idx, "gemini_response"] = ask_gemini(gemini_model, prompt)
            time.sleep(1.5)

        if not row.get("groq_response"):
            df.at[idx, "groq_response"] = ask_groq(groq_client, groq_model, prompt)
            time.sleep(1.5)

    df.to_csv(output_csv, index=False)
    print(f"Saved results to: {output_csv}")
    print("Stress test run completed.")

    return output_csv


if __name__ == "__main__":
    default_csv = Path("stress_test_prompts/stress_test_prompts.csv")

    if not default_csv.exists():
        print("File not found: stress_test_prompts/stress_test_prompts.csv")
        print("Run with: python stress_test_runner.py <path_to_csv>")
    else:
        run_stress_tests(default_csv)
