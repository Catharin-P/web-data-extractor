# summarizer.py
import os
import config
from openai import OpenAI
import traceback

class TextSummarizer:
    def __init__(self):
        """Initializes the OpenAI client using the API key from the config file."""
        api_key = getattr(config, 'OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY'))
        if not api_key:
            print("CRITICAL ERROR: OpenAI API key not found in config.py.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("OpenAI client initialized successfully with GPT-4o-mini.")

    def summarize_page(self, text: str, url: str, max_text_length=50000) -> str:
        """Summarizes the content of a SINGLE web page."""
        if not self.client:
            return "Summarizer not initialized."
        if not text or not text.strip():
            return "No text content on this page."

        if len(text) > max_text_length:
            print(f"  - WARNING: Text for {url} is very long. Truncating for page summary.")
            text = text[:max_text_length]

        system_prompt = "You are an expert analyst. Your task is to describe the primary purpose of a single web application page based on its text content."
        user_prompt = f"Based on the text below from the page '{url}', what is the main function or purpose of this page? Be concise.\n\n---\n\n{text}"

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=150,
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            print(f"  - ERROR during page summarization for {url}.")
            print(traceback.format_exc())
            return "Could not summarize page content due to an API error."