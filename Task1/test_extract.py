"""Quick test of regex extraction and title detection."""
import sys, os
sys.path.insert(0, os.getcwd())

from utils.utils import extract_headings_regex, extract_document_title_from_text
from langchain_text_splitters import RecursiveCharacterTextSplitter

MD_PATH = os.path.join("data", "Markdowns",
                       "FetchRobotics_CartConnect100_UnpackChargeRepackRev04.md")

with open(MD_PATH, encoding="utf-8") as f:
    text = f.read()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=2500, chunk_overlap=0,
    separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_text(text)
print(f"Chunks: {len(chunks)}")

title = extract_document_title_from_text(text)
print(f"Title: {title}")
print()

all_headings = [title] if title else []
for i, chunk in enumerate(chunks):
    h = extract_headings_regex(chunk)
    for hh in h:
        hh["chunk_index"] = i
    all_headings.extend(h)
    print(f"Chunk {i+1}: {len(h)} headings")

print()
print("ALL HEADINGS:")
for h in all_headings:
    lvl = h["level"]
    txt = h["text"]
    print(f"  [L{lvl}] {txt}")
