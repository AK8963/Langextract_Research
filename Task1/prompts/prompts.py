import textwrap
import langextract as lx


# Main extraction prompt
EXTRACTION_PROMPT = textwrap.dedent("""
TASK: Extract ONLY true structural headings that appear EXACTLY in this document text.
 
CRITICAL RULES:
1. ONLY extract headings that appear VERBATIM in the text - do NOT invent or hallucinate headings
2. Extract the EXACT text as it appears - do not paraphrase or modify
3. If unsure whether something is a heading, DO NOT extract it
 
WHAT IS A HEADING:
- Document/Report titles (first major title)
- Chapter titles ("Chapter 1", "Part I")
- Numbered sections: "1 Introduction", "2 Methods", "3. Results"
- Numbered subsections: "1.1 Background", "2.1 Data", "3.1.1 Analysis"
- Named standalone sections: "Abstract", "Conclusion", "References"
 
WHAT IS NOT A HEADING (DO NOT EXTRACT):
- Figure captions: "Figure 1:", "Fig. 2 shows..."
- Table captions: "Table 1:", "Table 2 displays..."
- Body text sentences or paragraphs
- Bullet points or list items
- Equations or formulas
- Page numbers: "Page 1", "1", "Page 2 of 10"
- Metadata: "DOI", "ISBN", "Thesis", "CITATIONS"
- Author names or affiliations
- Code snippets
 
HEADING LEVELS:
Level 1 → Document title, Chapter ("Machine Learning", "Chapter 3")
Level 2 → Major section ("1 Introduction", "2 Methods", "Conclusion")
Level 3 → Subsection ("1.1 Background", "2.1 Data Collection")
Level 4 → Sub-subsection ("1.1.1 History", "2.1.1 Sources")
 
ONLY return headings you are CERTAIN exist in the text.
""")


# Example extractions for few-shot learning
EXTRACTION_EXAMPLES = [
    # Example 1: Academic paper with numbered sections
    lx.data.ExampleData(
        text="""Machine Learning Methods
 
1 Introduction
Machine learning is a rapidly growing field.
Figure 1: Overview of ML types
Table 1: Comparison of algorithms
 
1.1 Background
The history of ML dates back to...
 
2 Methods
2.1 Data Collection
We collected data from...
 
Conclusion
In summary, this paper presented...
 
References
[1] Author et al.""",
        extractions=[
            lx.data.Extraction(extraction_class="heading", extraction_text="Machine Learning Methods", attributes={"level": 1}),
            lx.data.Extraction(extraction_class="heading", extraction_text="1 Introduction", attributes={"level": 2}),
            lx.data.Extraction(extraction_class="heading", extraction_text="1.1 Background", attributes={"level": 3}),
            lx.data.Extraction(extraction_class="heading", extraction_text="2 Methods", attributes={"level": 2}),
            lx.data.Extraction(extraction_class="heading", extraction_text="2.1 Data Collection", attributes={"level": 3}),
            lx.data.Extraction(extraction_class="heading", extraction_text="Conclusion", attributes={"level": 2}),
            lx.data.Extraction(extraction_class="heading", extraction_text="References", attributes={"level": 2}),
        ],
    ),
    # Example 2: Technical document with subsections
    lx.data.ExampleData(
        text="""3 Regression Methods
 
3.1 Linear Regression
Linear regression is a popular technique...
Figure 5: Illustration of linear fit
 
3.1.1 Simple Linear Regression
The basic model is Y = b0 + b1*X + e
 
3.1.2 Multiple Linear Regression
Most applications use more than one regressor.
 
3.2 Polynomial Regression
Polynomial regression extends linear models.
 
4 Application
We applied these methods to real data.""",
        extractions=[
            lx.data.Extraction(extraction_class="heading", extraction_text="3 Regression Methods", attributes={"level": 2}),
            lx.data.Extraction(extraction_class="heading", extraction_text="3.1 Linear Regression", attributes={"level": 3}),
            lx.data.Extraction(extraction_class="heading", extraction_text="3.1.1 Simple Linear Regression", attributes={"level": 4}),
            lx.data.Extraction(extraction_class="heading", extraction_text="3.1.2 Multiple Linear Regression", attributes={"level": 4}),
            lx.data.Extraction(extraction_class="heading", extraction_text="3.2 Polynomial Regression", attributes={"level": 3}),
            lx.data.Extraction(extraction_class="heading", extraction_text="4 Application", attributes={"level": 2}),
        ],
    ),
]
