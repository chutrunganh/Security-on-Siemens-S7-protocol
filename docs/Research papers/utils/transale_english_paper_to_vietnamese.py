import os
import time
import re
from deep_translator import GoogleTranslator

input_path = "/home/chutrunganh/Documents/HUST/Thesis/docs/Research papers/Masterarbeit_ICS_protocol_dissectors_for_signature_based_NIDS.md"
output_path = "/home/chutrunganh/Documents/HUST/Thesis/docs/Research papers/Masterarbeit_ICS_protocol_dissectors_for_signature_based_NIDS_VI.md"

def translate_markdown():
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Chunk by paragraph for safer translation and avoiding limits
    chunks = content.split("\n\n")
    translator = GoogleTranslator(source='auto', target='vi')
    
    translated_chunks = []
    
    print(f"Total chunks to translate: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            translated_chunks.append(chunk)
            continue
            
        # Skip pure code blocks
        if chunk.strip().startswith("```"):
            translated_chunks.append(chunk)
            continue
            
        # Check if table (basic check), skip full table translation that breaks formatting
        if "|" in chunk and "---" in chunk and chunk.count("|") > max(2, len(chunk.split("\n"))):
            translated_chunks.append(chunk)
            continue
            
        # Extract inline words to preserve them (like specialized terms in backticks)
        # We replace them with placeholders so Google Translator doesn't alter them
        code_blocks = re.findall(r'`[^`]+`', chunk)
        placeholders = {}
        for idx, cb in enumerate(code_blocks):
            placeholder = f"__CODE_BLOCK_{idx}__"
            chunk = chunk.replace(cb, placeholder)
            placeholders[placeholder] = cb
            
        try:
            # The chunk limit for google translator is 5000 chars, so we handle long chunks
            if len(chunk) > 4900:
                t_subchunks = []
                for j in range(0, len(chunk), 4900):
                    sc = chunk[j:j+4900]
                    t_subchunks.append(translator.translate(sc))
                t_chunk = "".join(t_subchunks)
            else:
                t_chunk = translator.translate(chunk)
                
            # Restore code blocks back
            for placeholder, cb in placeholders.items():
                t_chunk = t_chunk.replace(placeholder, cb)
                
            translated_chunks.append(t_chunk)
            
        except Exception as e:
            print(f"Error at chunk {i}: {e}. Retrying after 5 seconds...")
            time.sleep(5)
            try:
                # retry once
                t_chunk = translator.translate(chunk)
                for placeholder, cb in placeholders.items():
                    t_chunk = t_chunk.replace(placeholder, cb)
                translated_chunks.append(t_chunk)
            except:
                print(f"Failed again at chunk {i}. Keeping original.")
                translated_chunks.append(chunk) # append original on fail
            
        if (i+1) % 10 == 0:
            print(f"Translated {i+1}/{len(chunks)} chunks...")
            # slow down to avoid IP ban or rate limits
            time.sleep(1)
            
        # Intermediate saves to not lose progress in case of crash
        if (i+1) % 100 == 0:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(translated_chunks))
            
    # Final save
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(translated_chunks))
        
    print(f"Successfully finished translation. Saved to {output_path}")

if __name__ == "__main__":
    translate_markdown()
