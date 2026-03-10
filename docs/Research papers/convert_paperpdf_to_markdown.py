from docling.document_converter import DocumentConverter
from pathlib import Path

source = "/home/chutrunganh/Documents/HUST/Thesis/docs/Research papers/Masterarbeit_ICS_protocol_dissectors_for_signature_based_NIDS.pdf"
output_path = "/home/chutrunganh/Documents/HUST/Thesis/docs/Research papers/Masterarbeit_ICS_protocol_dissectors_for_signature_based_NIDS_docling.md"

print(f"Converting {source}...")
converter = DocumentConverter()
result = converter.convert(source)

# Export to markdown
markdown_output = result.document.export_to_markdown()

# Store to file
with open(output_path, "w", encoding="utf-8") as f:
    f.write(markdown_output)

print(f"Successfully saved to {output_path}")