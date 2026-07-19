"""
Utility functions for automation processing.

This file is the "fill-in-the-blanks" tool of the WebAI API server
(see walkthrough.md → "Component 1: The Warehouse" → Variable Substitution).

Recorded steps can contain placeholders like `{{irctc_username}}`. At
playback time the API merges the user's config (plain variables + decrypted
secrets) and `substitute_variables()` replaces every placeholder with its
real value, so the browser robot receives concrete steps with no secrets
left in the database.

Other helpers:
- `extract_variables_from_steps` — list which placeholders a recording uses
  (useful for prompting the user to fill them in).
- `validate_config_variables` — check that every placeholder has a value.
- `merge_secrets_with_variables` — combine plain variables and decrypted
  secrets into one dict for substitution.
"""
import re
import json
from typing import List, Dict, Any


def substitute_variables(steps_json: List[Dict[str, Any]], config_variables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Replace {{variable_name}} placeholders with actual values from config
    
    Args:
        steps_json: List of step dictionaries with potential {{variable}} placeholders
        config_variables: Dictionary of variable names to values
    
    Returns:
        List of steps with all variables substituted
    
    Example:
        steps = [{"action": "wait", "value": "{{user_wait_time}}"}]
        config = {"user_wait_time": 5}
        result = substitute_variables(steps, config)
        # Returns: [{"action": "wait", "value": 5}]
    """
    # Convert to string for regex replacement
    steps_str = json.dumps(steps_json)
    
    # Find all {{variable}} patterns
    pattern = r'\{\{(\w+)\}\}'
    
    def replace_var(match):
        var_name = match.group(1)
        if var_name in config_variables:
            value = config_variables[var_name]
            # Return JSON-encoded value for proper type preservation
            if isinstance(value, str):
                return json.dumps(value)
            else:
                return json.dumps(value)
        else:
            # Variable not found - keep placeholder and warn
            print(f"⚠️ Variable '{var_name}' not found in config, keeping placeholder")
            return match.group(0)
    
    # Replace all variables
    steps_str = re.sub(pattern, replace_var, steps_str)
    
    return json.loads(steps_str)


def extract_variables_from_steps(steps_json: List[Dict[str, Any]]) -> List[str]:
    """
    Extract all {{variable}} placeholders from steps
    
    Args:
        steps_json: List of step dictionaries
    
    Returns:
        List of unique variable names found
    
    Example:
        steps = [
            {"action": "type", "value": "{{username}}"},
            {"action": "wait", "value": "{{wait_time}}"}
        ]
        result = extract_variables_from_steps(steps)
        # Returns: ["username", "wait_time"]
    """
    steps_str = json.dumps(steps_json)
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, steps_str)
    return list(set(matches))  # Return unique variables


def validate_config_variables(steps_json: List[Dict[str, Any]], config_variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required variables from steps are present in config
    
    Args:
        steps_json: List of step dictionaries
        config_variables: Dictionary of provided variables
    
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "missing_variables": List[str],
            "unused_variables": List[str]
        }
    """
    required_vars = set(extract_variables_from_steps(steps_json))
    provided_vars = set(config_variables.keys())
    
    missing = list(required_vars - provided_vars)
    unused = list(provided_vars - required_vars)
    
    return {
        "valid": len(missing) == 0,
        "missing_variables": missing,
        "unused_variables": unused
    }


def merge_secrets_with_variables(variables: Dict[str, Any], decrypted_secrets: Dict[str, str]) -> Dict[str, Any]:
    """
    Merge decrypted secrets with regular variables for substitution
    
    Args:
        variables: Regular configuration variables
        decrypted_secrets: Decrypted credential dictionary
    
    Returns:
        Merged dictionary of all values for substitution
    """
    merged = variables.copy()
    merged.update(decrypted_secrets)
    return merged
