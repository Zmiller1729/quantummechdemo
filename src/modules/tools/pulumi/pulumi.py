from .refactor import (
    refactor,
)
function_map = {
    # Existing functions...
    "refactor": refactor,
}
tools = [
    # Existing tools...
    {
        "type": "function",
        "name": "refactor",
        "description": (
            "Analyzes code to identify poorly named variables and Pulumi resources, "
            "suggests replacements with confidence scores, and writes results to a file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the code file to analyze and refactor.",
                },
            },
            "required": ["file_path"],
        },
    },
]
