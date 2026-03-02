import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import is_page_marker


def build_hierarchical_chunks(sections: list) -> list:
    """
    Build hierarchical JSON chunks with Parent, Main, Sub headings and combined Text.
    
    DYNAMIC CHUNKING: Creates chunks based on document structure, not fixed targets.
    - Each Level-1 heading starts a new chunk
    - Level-2 headings can start new chunks if they represent major sections
    - Subsections (Level 3+) stay with their parent heading
    """
    if not sections:
        return []
    
    # Dynamic chunking based on document structure
    chunk_boundaries = []
    current_chunk_start = 0
    items_in_current = 0
    has_subsections_in_current = False
    
    for i, sec in enumerate(sections):
        items_in_current = i - current_chunk_start
        
        if sec["level"] == 1 and i > 0:
            chunk_boundaries.append(i)
            current_chunk_start = i
            has_subsections_in_current = False
            
        elif sec["level"] == 2 and i > 0:
            if items_in_current >= 2 or has_subsections_in_current:
                chunk_boundaries.append(i)
                current_chunk_start = i
                has_subsections_in_current = False
                
        elif sec["level"] >= 3:
            has_subsections_in_current = True
    
    chunk_boundaries.append(len(sections))
    
    # Build chunks
    output_chunks = []
    chunk_id = 1
    start_idx = 0
    
    for boundary in chunk_boundaries:
        chunk_sections = sections[start_idx:boundary]
        if not chunk_sections:
            continue
        
        chunk_data = {}
        chunk_text_parts = []
        
        main_heading_counter = 1
        sub_heading_counter = 1
        current_main_heading = None
        current_details = {}
        details_key = None
        
        # Find parent heading (level 1) if exists
        parent_heading = None
        for sec in chunk_sections:
            if sec["level"] == 1:
                parent_heading = sec["text"]
                break
        
        # If no level 1 in this chunk, check if there's one earlier
        if not parent_heading and start_idx > 0:
            for sec in reversed(sections[:start_idx]):
                if sec["level"] == 1:
                    parent_heading = sec["text"]
                    break
        
        if parent_heading:
            chunk_data["Parent Heading"] = f"{parent_heading} ....."
        
        for sec in chunk_sections:
            level = sec["level"]
            heading_text = sec["text"]
            content = sec["content"]
            
            # Skip page markers
            if is_page_marker(heading_text):
                continue
            
            # Add to text
            chunk_text_parts.append(heading_text)
            if content:
                chunk_text_parts.append(content)
            
            if level == 1:
                continue
            elif level == 2:
                # Save any pending details
                if current_details and details_key:
                    chunk_data[details_key] = current_details
                    current_details = {}
                    details_key = None
                
                # Add main heading
                key = f"Main Heading {main_heading_counter}"
                chunk_data[key] = f"{heading_text} ....."
                current_main_heading = heading_text
                main_heading_counter += 1
                sub_heading_counter = 1
                
            elif level >= 3:
                # Sub heading - add to details
                if current_main_heading and not details_key:
                    details_key = f"{current_main_heading} Details"
                    current_details = {}
                
                if details_key:
                    sub_key = f"Sub Heading {sub_heading_counter}"
                    current_details[sub_key] = f"{heading_text} ....."
                    sub_heading_counter += 1
                else:
                    key = f"Main Heading {main_heading_counter}"
                    chunk_data[key] = f"{heading_text} ....."
                    main_heading_counter += 1
        
        # Save final pending details
        if current_details and details_key:
            chunk_data[details_key] = current_details
        
        # Combine text
        combined_text = "\n".join(chunk_text_parts)
        combined_text = re.sub(r'\n{3,}', '\n\n', combined_text)
        
        output_chunks.append({
            f"chunk_id{chunk_id}": chunk_data,
            "Text": combined_text
        })
        
        chunk_id += 1
        start_idx = boundary
    
    return output_chunks
