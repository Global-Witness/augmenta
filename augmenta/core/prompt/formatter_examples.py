import yaml
import json
from xml.sax.saxutils import escape

class ExampleFormatter:
    """Formats examples for prompt creation"""
    
    @staticmethod
    def format_examples(examples_yaml: str) -> str:
        """Format YAML examples into XML structure"""
        try:
            # Parse YAML
            data = yaml.safe_load(examples_yaml)
            
            if not data or 'examples' not in data:
                return ""
            
            # Process each example
            formatted_examples = []
            for example in data['examples']:
                input_text = example['input']
                output_dict = example['output']
                
                # Convert output to JSON string, ensuring proper escaping
                output_json = json.dumps(output_dict, ensure_ascii=False)
                
                # Create XML structure for this example
                example_xml = (
                    f'<example>\n'
                    f'<input>{escape(input_text)}</input>\n'
                    f'<ideal_output>{escape(output_json)}</ideal_output>\n'
                    f'</example>'
                )
                formatted_examples.append(example_xml)
            
            # Combine all examples
            examples_xml = '\n'.join(formatted_examples)
            return f"## Examples\n<examples>\n{examples_xml}\n</examples>"
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in examples: {e}")