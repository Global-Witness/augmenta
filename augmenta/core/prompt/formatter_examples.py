"""Example formatting utilities for prompt creation."""

from typing import Dict, Any
import yaml
import json
from xml.sax.saxutils import escape

class ExampleFormatter:
    """Formats examples for prompt creation using XML structure."""
    
    @staticmethod
    def format_examples(examples_yaml: str) -> str:
        """
        Format YAML examples into XML structure.
        
        Args:
            examples_yaml: YAML string containing example data
            
        Returns:
            str: Formatted XML string containing examples
            
        Raises:
            ValueError: If YAML is invalid or missing required fields
        """
        try:
            data: Dict[str, Any] = yaml.safe_load(examples_yaml)
            
            if not data or 'examples' not in data:
                return ""
            
            examples = []
            for example in data['examples']:
                if not isinstance(example, dict) or 'input' not in example or 'output' not in example:
                    raise ValueError("Each example must contain 'input' and 'output' fields")
                
                output_json = json.dumps(example['output'], ensure_ascii=False)
                example_xml = (
                    f'<example>'
                    f'<input>{escape(str(example["input"]))}</input>'
                    f'<ideal_output>{escape(output_json)}</ideal_output>'
                    f'</example>'
                )
                examples.append(example_xml)
            
            return f"## Examples\n<examples>\n{''.join(examples)}\n</examples>"
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")