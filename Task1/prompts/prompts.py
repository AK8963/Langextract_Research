import textwrap
import langextract as lx


# Main extraction prompt
EXTRACTION_PROMPT = textwrap.dedent("""
TASK: Extract ONLY true structural headings from this document text chunk.

CRITICAL RULES:
1. ONLY extract headings that appear VERBATIM as their own line in the chunk—do NOT invent headings.
2. Return the exact heading text with any leading `#` characters and surrounding `**` bold markers stripped.
3. Numbered single-digit sections like "1. OVERVIEW" or "3. UNPACK PROCESS" are MAIN SECTIONS → level 2.
4. Sub-sections with x.y numbering like "1.1 Introduction" → level 3.
5. Sub-sub-sections with x.y.z → level 4.
6. NEVER extract table rows (lines containing |), bullet list items (lines starting with -, *, ✓, or **1.**),
   body text sentences, image captions, cross-references, or page footers.
7. Do NOT extract document-wide disclaimers like "Confidential Information" or proprietary notices.
8. If uncertain, do not extract.

WHAT COUNTS AS A HEADING:
- A line beginning with one or more `#` markdown symbols (e.g., `#### 2. INSPECTION PROCESS`)
- A standalone short line with a section prefix (e.g., "2. INSPECTION PROCESS", "1.1 Overview")

LEVEL RULES:
- Single-digit numbered sections (1., 2., 3. …) → level 2
- Two-part numbered sections (1.1, 2.3 …) → level 3
- Three-part numbered sections (1.1.1, 2.3.1 …) → level 4
- If no numbering, use markdown `#` count as level
""")


# Example extractions for few-shot learning
EXTRACTION_EXAMPLES = [
    # Example 0: Work instruction document with numbered sections (mirrors the target doc type)
    lx.data.ExampleData(
        text="""#### 1. OVERVIEW

The purpose of this work instruction is to provide the procedure.

#### 2. INSPECTION PROCESS

- **1.** Move the robot to the staging area.
- **2.** Inspect the shipment.

#### 3. UNPACK PROCESS

- **1.** Move the freight crate to the charging area.

## 5. REFERENCES

| Document # | Document Title |

### 6. REVISION HISTORY

The following table lists all revisions.""",
        extractions=[
            lx.data.Extraction(extraction_class="heading", extraction_text="1. OVERVIEW", attributes={"level": 2, "confidence": 0.99}),
            lx.data.Extraction(extraction_class="heading", extraction_text="2. INSPECTION PROCESS", attributes={"level": 2, "confidence": 0.99}),
            lx.data.Extraction(extraction_class="heading", extraction_text="3. UNPACK PROCESS", attributes={"level": 2, "confidence": 0.99}),
            lx.data.Extraction(extraction_class="heading", extraction_text="5. REFERENCES", attributes={"level": 2, "confidence": 0.98}),
            lx.data.Extraction(extraction_class="heading", extraction_text="6. REVISION HISTORY", attributes={"level": 2, "confidence": 0.98}),
        ],
    ),
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
