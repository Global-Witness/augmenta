from typing import List, Tuple, Optional
from xml.sax.saxutils import escape
import yaml
import json

def format_xml_content(tag: str, content: str) -> str:
    """Helper to format XML content with escaping"""
    return f"<{tag}>{escape(content)}</{tag}>"

def format_docs(scraped_content: List[Tuple[str, Optional[str]]]) -> str:
    """Formats scraped content into XML structure"""
    if not scraped_content:
        return "<documents></documents>"

    documents = [
        f'<document index="{i}">'
        f'{format_xml_content("source", url)}'
        f'{format_xml_content("document_content", text)}'
        f'</document>'
        for i, (url, text) in enumerate(
            ((url, text) for url, text in scraped_content if text),
            start=1
        )
    ]

    return f"<documents>{''.join(documents)}</documents>"

def format_examples(examples_yaml: str) -> str:
    """Formats YAML examples into XML structure"""
    try:
        data = yaml.safe_load(examples_yaml)
        if not data or 'examples' not in data:
            return ""
        
        examples = []
        for example in data['examples']:
            if not isinstance(example, dict) or 'input' not in example or 'output' not in example:
                raise ValueError("Each example must contain 'input' and 'output' fields")
            
            output_json = json.dumps(example['output'], ensure_ascii=False)
            example_xml = (
                '<example>'
                f'{format_xml_content("input", str(example["input"]))}'
                f'{format_xml_content("ideal_output", output_json)}'
                '</example>'
            )
            examples.append(example_xml)
        
        return f"## Examples\n<examples>\n{''.join(examples)}\n</examples>"
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}")