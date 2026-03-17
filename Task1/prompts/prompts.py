import textwrap
import langextract as lx


# Main extraction prompt
EXTRACTION_PROMPT = textwrap.dedent("""
TASK: Extract ONLY true structural headings from this markdown document text. You will be given a chunk
of the document. Extract only headings that are present verbatim as lines in this chunk.

CRITICAL RULES (reduce false positives):
1. ONLY extract headings that appear VERBATIM as their own line in the chunk—do NOT invent or hallucinate headings.
2. Return the exact heading text as it appears (but strip leading `#` characters and surrounding `**` bold markers).
3. If a heading line begins with `#` characters, the level is equal to the number of `#` characters.
4. If the line is a numbered heading (e.g., "1.", "1.1"), set the level by numbering only when no `#` is present.
5. DO NOT extract table rows, bullet items, code, captions, or inline sentences—only standalone heading lines.
6. If unsure, do not extract.

MARKDOWN RULES:
- `# Title` → level 1
- `## Section` → level 2
- `### Subsection` → level 3
- `#### Sub-subsection` → level 4
- `##### Deep section` → level 5

OUTPUT FORMAT:
- Return a JSON array (no surrounding text) where each item is an object with keys: `text` (string), `level` (integer).
- `text` must be the heading as it appears in the document line, with any leading `#` and surrounding `**` removed.
- `level` must reflect the number of `#` if present; otherwise a sensible numeric level based on numbering.
- `confidence` (optional): a float between 0 and 1 indicating how confident you are that this is a true heading in the provided chunk. If included, higher values indicate higher confidence.

EXTRA EXAMPLE (few-shot):
Chunk input:
'''
# **Sales Analysis Report**

### **Executive Summary**

Some paragraph.

## Methodology
'''

Desired JSON output (exact):
[ {"text": "Sales Analysis Report", "level": 1, "confidence": 0.98},
  {"text": "Executive Summary", "level": 3, "confidence": 0.95},
  {"text": "Methodology", "level": 2, "confidence": 0.96} ]

ONLY return headings you are CERTAIN are markdown heading lines in the chunk.
""")


# Example extractions for few-shot learning
EXTRACTION_EXAMPLES = [
    # Example 1: Markdown report with mixed heading levels
    lx.data.ExampleData(
        text="""# **Sales Analysis Report**

### **Executive Summary**

This report covers two months of sales data with key trends.

## **Methodology**

- Data extraction using SQL and Python
- Tableau visualization for reporting

## **Key Findings**

### **Sales Performance**

- Overall revenue growth of 15%
- Top 3 products contribute 65% of revenue

### **Customer Behavior**

- Average transaction value increased by 12%

| Month | Revenue |
|-------|---------|
| Jan   | $308,000 |
| Feb   | $354,200 |
""",
        extractions=[
            lx.data.Extraction(extraction_class="heading", extraction_text="Sales Analysis Report", attributes={"level": 1, "confidence": 0.98}),
            lx.data.Extraction(extraction_class="heading", extraction_text="Executive Summary", attributes={"level": 3, "confidence": 0.95}),
            lx.data.Extraction(extraction_class="heading", extraction_text="Methodology", attributes={"level": 2, "confidence": 0.96}),
            lx.data.Extraction(extraction_class="heading", extraction_text="Key Findings", attributes={"level": 2, "confidence": 0.93}),
            lx.data.Extraction(extraction_class="heading", extraction_text="Sales Performance", attributes={"level": 3, "confidence": 0.92}),
            lx.data.Extraction(extraction_class="heading", extraction_text="Customer Behavior", attributes={"level": 3, "confidence": 0.92}),
        ],
    ),
    # Example 2: Markdown with deep nesting and code blocks
    lx.data.ExampleData(
        text="""## **1. Data Collection & Preparation**

#### **1.1 Data Sources**

```sql
SELECT date, product_id, sales_amount
FROM sales_transactions
WHERE date BETWEEN '2024-01-01' AND '2024-02-29'
```

#### **1.2 Data Cleaning (Python)**

```python
import pandas as pd
def clean_sales_data(df):
    df = df.drop_duplicates()
    return df
```

## **2. Analysis Process**

##### **2.1 Excel Analysis**

- Created pivot tables for initial data exploration
- Developed automated reports

##### **2.2 Python Analysis**

- Customer segmentation applied
""",
        extractions=[
            lx.data.Extraction(extraction_class="heading", extraction_text="1. Data Collection & Preparation", attributes={"level": 2, "confidence": 0.97}),
            lx.data.Extraction(extraction_class="heading", extraction_text="1.1 Data Sources", attributes={"level": 4, "confidence": 0.95}),
            lx.data.Extraction(extraction_class="heading", extraction_text="1.2 Data Cleaning (Python)", attributes={"level": 4, "confidence": 0.94}),
            lx.data.Extraction(extraction_class="heading", extraction_text="2. Analysis Process", attributes={"level": 2, "confidence": 0.96}),
            lx.data.Extraction(extraction_class="heading", extraction_text="2.1 Excel Analysis", attributes={"level": 5, "confidence": 0.92}),
            lx.data.Extraction(extraction_class="heading", extraction_text="2.2 Python Analysis", attributes={"level": 5, "confidence": 0.92}),
        ],
    ),
]
