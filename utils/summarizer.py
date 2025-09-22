# summarizer.py
from transformers import pipeline

class TextSummarizer:
    def __init__(self, model="t5-small"):
        """Initializes the summarization pipeline."""
        print(f"Loading summarization model ({model})... This may take a moment.")
        # For higher quality summaries, consider "facebook/bart-large-cnn"
        # For speed and lower resource usage, "t5-small" is a good choice.
        self.summarizer = pipeline(
            "summarization", 
            model=model, 
            tokenizer=model
        )
        print("Model loaded successfully.")

    def summarize(self, text: str, max_chunk_length=512) -> str:
        """
        Summarizes a piece of text. Handles long text by breaking it into chunks.
        """
        if not text.strip():
            return "No content to summarize."
        
        try:
            # The model has a max token limit, so we summarize long texts in chunks.
            tokens = self.summarizer.tokenizer.tokenize(text)
            chunks = [tokens[i:i + max_chunk_length] for i in range(0, len(tokens), max_chunk_length)]
            decoded_chunks = [self.summarizer.tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks]
            
            summaries = self.summarizer(
                decoded_chunks, 
                max_length=150, 
                min_length=30, 
                do_sample=False
            )
            
            return ' '.join([summary['summary_text'] for summary in summaries])
        except Exception as e:
            print(f"Error during summarization: {e}")
            return "Could not summarize content."