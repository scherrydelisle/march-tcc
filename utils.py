from typing import List 

ANTHROPIC_API_KEY = "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"

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""

    chunks = []
    sentences = text.split('. ') 
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip() + '. '
        sentence_length = len(sentence)
        
        if current_length + sentence_length > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            overlap_text = ' '.join(current_chunk[-2:])
            current_chunk = [overlap_text]
            current_length = len(overlap_text)
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def visualize_citations(response):
    """
    Takes a response object and returns a string with numbered citations.
    Example output: "here is the plain text answer [1][2] here is some more text [3]"
    with a list of citations below.
    """
    # Dictionary to store unique citations
    citations_dict = {}
    citation_counter = 1
    
    # Final formatted text
    formatted_text = ""
    citations_list = []

    print("\n" + "="*80 + "\nFormatted response:\n" + "="*80)
    
    for content in response.content:
        if content.type == "text":
            text = content.text
            if hasattr(content, 'citations') and content.citations:
                # Sort citations by their appearance in the text
                def get_sort_key(citation):
                    if hasattr(citation, 'start_char_index'):
                        return citation.start_char_index
                    elif hasattr(citation, 'start_page_number'):
                        return citation.start_page_number
                    elif hasattr(citation, 'start_block_index'):
                        return citation.start_block_index
                    return 0  # fallback

                sorted_citations = sorted(content.citations, key=get_sort_key)
                
                # Process each citation
                for citation in sorted_citations:
                    doc_title = citation.document_title
                    cited_text = citation.cited_text.replace('\n', ' ').replace('\r', ' ')
                    # Remove any multiple spaces that might have been created
                    cited_text = ' '.join(cited_text.split())
                    
                    # Create a unique key for this citation
                    citation_key = f"{doc_title}:{cited_text}"
                    
                    # If this is a new citation, add it to our dictionary
                    if citation_key not in citations_dict:
                        citations_dict[citation_key] = citation_counter
                        citations_list.append(f"[{citation_counter}] \"{cited_text}\" found in \"{doc_title}\"")
                        citation_counter += 1
                    
                    # Add the citation number to the text
                    citation_num = citations_dict[citation_key]
                    text += f" [{citation_num}]"
            
            formatted_text += text
    
    # Combine the formatted text with the citations list
    final_output = formatted_text + "\n\n" + "\n".join(citations_list)
    return final_output
