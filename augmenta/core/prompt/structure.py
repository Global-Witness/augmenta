from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class StructureField:
    type: str
    description: str

class StructureFormatter:
    """Formats structure definitions into prompt sections"""

    @staticmethod
    def format_structure(structure: Dict[str, Dict[str, str]]) -> str:
        """
        Convert a structure definition into a response format section
        
        Args:
            structure: Dictionary of field definitions from YAML
            
        Returns:
            Formatted string describing the expected response format
        """
        # Start with the response format header
        output = ["# Response format", "Your response should be in JSON format and include the following fields:"]
        
        # Add each field with its description
        for field_name, field_def in structure.items():
            # Handle both string and dict descriptions
            if isinstance(field_def, dict):
                description = field_def.get('description', '')
            else:
                description = str(field_def)
                
            output.append(f"- `{field_name}`: {description}")
        
        return "\n".join(output)

    @staticmethod
    def append_structure_to_prompt(prompt: str, structure: Dict[str, Dict[str, str]]) -> str:
        """
        Append structure format to an existing prompt
        
        Args:
            prompt: Original prompt text
            structure: Structure definition from YAML
            
        Returns:
            Combined prompt with response format
        """
        structure_text = StructureFormatter.format_structure(structure)
                
        # Otherwise append it
        return f"{prompt.rstrip()}\n\n{structure_text}"
