import os
import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser

def convert_pdf_to_markdown(pdf_path: str, output_md_path: str, ollama_model: str, ollama_base_url: str = "http://localhost:11434"):
    """
    Converts a PDF file to a markdown file using an Ollama model.

    Args:
        pdf_path (str): The full path to the source PDF file.
        output_md_path (str): The full path where the output markdown file will be saved.
        ollama_model (str): The name of the Ollama model to use (e.g., "gemma2:2b").
        ollama_base_url (str, optional): The base URL for the Ollama service. Defaults to "http://localhost:11434".
    """
    print(f"Starting conversion for: {pdf_path}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # 1. Set up the configuration for marker-pdf
    config = {
        "llm_service": "marker.services.ollama.OllamaService",
        "ollama_model": ollama_model,
        "ollama_base_url": ollama_base_url,
        "output_format": "markdown",
        "device": device
    }

    # 2. Initialize the converter
    config_parser = ConfigParser(config)
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service()
    )

    # 3. Perform the conversion
    rendered = converter(pdf_path)
    text, _, _ = text_from_rendered(rendered)

    # 4. Save the output file
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_md_path)
    os.makedirs(output_dir, exist_ok=True)

    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Successfully converted PDF to markdown and saved as {output_md_path}")


# --------------- If LLM is not needed ------------------
# import os
# import torch
# from marker.converters.pdf import PdfConverter
# from marker.models import create_model_dict
# from marker.output import text_from_rendered
# from marker.config.parser import ConfigParser

# def convert_pdf_to_markdown(pdf_path: str, output_md_path: str):
#     """
#     Converts a PDF file to a markdown file using marker-pdf.

#     Args:
#         pdf_path (str): The full path to the source PDF file.
#         output_md_path (str): The full path where the output markdown file will be saved.
#     """
#     print(f"Starting conversion for: {pdf_path}")
    
#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     print(f"Using device: {device}")

#     # 1. Set up the configuration for marker-pdf
#     config = {
#         "output_format": "markdown",
#         "device": device
#     }

#     # 2. Initialize the converter
#     config_parser = ConfigParser(config)
#     converter = PdfConverter(
#         config=config_parser.generate_config_dict(),
#         artifact_dict=create_model_dict(),
#         processor_list=config_parser.get_processors(),
#         renderer=config_parser.get_renderer()
#     )

#     # 3. Perform the conversion
#     rendered = converter(pdf_path)
#     text, _, _ = text_from_rendered(rendered)

#     # 4. Save the output file
#     # Ensure the output directory exists
#     output_dir = os.path.dirname(output_md_path)
#     os.makedirs(output_dir, exist_ok=True)

#     with open(output_md_path, "w", encoding="utf-8") as f:
#         f.write(text)

#     print(f"Successfully converted PDF to markdown and saved as {output_md_path}")


# # --- Example of how to use the function ---
# if __name__ == "__main__":
#     # Find the main config.json file
#     config_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "config", "config.json"))

#     import json
#     try:
#         with open(config_path, "r", encoding="utf-8") as cf:
#             file_cfg = json.load(cf)
#     except Exception as e:
#         raise SystemExit(f"Error reading config file at {config_path}: {e}")

#     # Get PDF source path from the config file
#     pdf_source = file_cfg.get("pdf_source")
#     if not pdf_source:
#         raise SystemExit("pdf_source not found in config.json; please add 'pdf_source' key")

#     # Get markdown output path from the config file
#     try:
#         output_md = file_cfg["output"]["markdown_path"]
#     except KeyError:
#         raise SystemExit("output.markdown_path not found in config.json; please add 'output': {'markdown_path': '...'}")

#     # Resolve paths relative to the config file's directory
#     config_dir = os.path.dirname(config_path)
#     if not os.path.isabs(pdf_source):
#         pdf_source = os.path.normpath(os.path.join(config_dir, pdf_source))

#     if not os.path.isabs(output_md):
#         output_md_path = os.path.normpath(os.path.join(config_dir, output_md))
#     else:
#         output_md_path = output_md

#     # Call the main function to perform the conversion
#     convert_pdf_to_markdown(
#         pdf_path=pdf_source,
#         output_md_path=output_md_path
#     )

