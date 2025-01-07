import os
import ast
import json
import time
import logging
import asyncio
import re
from typing import List, Optional
from rope.base.exceptions import BadIdentifierError

# Define a stricter identifier regex
identifier_regex = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\Z')

from pydantic import BaseModel, Field
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.base import libutils

 # Configure logging to show DEBUG messages
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger("assistant").setLevel(logging.DEBUG)

class NamingFinding(BaseModel):
    severity: int = Field(..., description="Severity level from 1 (Trivial) to 5 (Critical)")
    line_number: int = Field(..., description="Line number where the finding is located")
    original_name: str = Field(..., description="Original name")
    replacement_name: str = Field(..., description="Suggested replacement name")
    reason: str = Field(..., description="Reason for suggesting the replacement")

class VariableNamingFinding(NamingFinding):
    """Represents a finding of a poorly named variable and its suggested replacement."""
    pass

class ResourceNamingFinding(NamingFinding):
    """Represents a finding of a poorly named Pulumi resource and its suggested replacement."""
    pass

class VariableNamingFindingList(BaseModel):
    findings: List[VariableNamingFinding]

class ResourceNamingFindingList(BaseModel):
    findings: List[ResourceNamingFinding]

class RefactoringFindings(BaseModel):
    file: str = Field(..., description="File name")
    language: str = Field(..., description="Programming language (e.g., python, javascript, etc.)")
    variable_findings: VariableNamingFindingList = Field(..., description="Variable naming findings")
    resource_findings: ResourceNamingFindingList = Field(..., description="Resource naming findings")


# Centralized severity threshold
SEVERITY_THRESHOLD = 2  # Include findings with severity level 2 (Minor) and above

# Common severity criteria
SEVERITY_CRITERIA = """
<severity_criteria>
    <level value="5" name="Critical">
        <criterion>Nonsensical or meaningless names (e.g., `abc123`, `res123`)</criterion>
        <criterion>Names that are misleading relative to their usage or purpose</criterion>
    </level>
    <level value="4" name="Major">
        <criterion>Overly generic names that don't convey purpose (e.g., `data`, `resource`)</criterion>
        <criterion>Severe violations of naming conventions</criterion>
    </level>
    <level value="3" name="Moderate">
        <criterion>Names that could be more precise or descriptive</criterion>
        <criterion>Uses unclear abbreviations or acronyms</criterion>
    </level>
    <level value="2" name="Minor">
        <criterion>Slight ambiguity in the name</criterion>
        <criterion>Inconsistent naming conventions</criterion>
    </level>
    <level value="1" name="Trivial">
        <criterion>Minor stylistic improvements</criterion>
        <criterion>Names that could be slightly more consistent</criterion>
    </level>
</severity_criteria>
"""

# Common possible reasons
POSSIBLE_REASONS = """
<possible_reasons>
    <reason>Nonsensical or meaningless name</reason>
    <reason>Overly generic name</reason>
    <reason>Misleading name relative to usage</reason>
    <reason>Does not follow naming conventions</reason>
    <reason>Could be more precise</reason>
    <reason>Uses unclear abbreviation or acronym</reason>
    <reason>Inconsistent naming convention</reason>
    <reason>Minor improvement needed</reason>
    <reason>Slight ambiguity in name</reason>
    <reason>Other (If 'Other', please specify the reason)</reason>
</possible_reasons>
"""

# Define the scratch pad directory
scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

async def refactor_poorly_named_variables(file_path: str) -> Optional[VariableNamingFindingList]:
    """
    Analyzes the specified code file to identify poorly named variables and suggests replacements.

    Args:
        file_path (str): The path to the code file to analyze.

    Returns:
        Optional[VariableNamingFindingList]: A list of variable naming findings or None if an error occurs.
    """
    # Ensure the file exists
    if not os.path.exists(file_path):
        logging.error(f"File '{file_path}' does not exist.")
        return None

    # Read the code content
    try:
        with open(file_path, 'r') as file:
            code_content = file.read()
    except Exception as e:
        logging.error(f"Failed to read the file: {str(e)}")
        return None

    # Construct the system and user messages
    system_message = f"""
You are analyzing Python code to identify variables that are not clearly or well named. For each poorly named variable you find, assign a severity level based on specific criteria, provide a reason for suggesting a replacement, and suggest a replacement name.
Be sure to look at every variable in the code and provide a finding for each one that is poorly named.

<instructions>
You are analyzing Python code to identify variables that are not clearly or well named. For each poorly named variable:

1. Assign a **severity level** from 1 (Trivial) to 5 (Critical) based on how problematic the variable name is.
2. Provide a **reason** for suggesting a replacement, choosing from predefined reasons.
3. Suggest a **replacement name** that follows best practices and naming conventions.

Provide the findings as a list of JSON objects with the following fields:

- `severity`: (int)
- `line_number`: (int)
- `original_name`: (str)
- `replacement_name`: (str)
- `reason`: (str)

Ensure that the `original_name` and `replacement_name` fields only contain the variable names, without any additional code or context.

Do not report variables that are well-named and do not require any changes. Include all findings with a severity level of {SEVERITY_THRESHOLD} or higher.
</instructions>

{SEVERITY_CRITERIA}

{POSSIBLE_REASONS}

<examples>
    <!-- Specific Example -->
    <example>
        <code_snippet>
            IAMGroup00cloudtrailaccess00tWg7V = iam.Group('IAMGroup00cloudtrailaccess00tWg7V')
        </code_snippet>
        <finding>
            <severity>5</severity>
            <line_number>23</line_number>
            <original_name>IAMGroup00cloudtrailaccess00tWg7V</original_name>
            <replacement_name>cloudtrail_access_group</replacement_name>
            <reason>Nonsensical or meaningless name</reason>
        </finding>
    </example>
    <!-- Templated Example -->
    <example>
        <code_snippet>
            {{original_variable_code}}
        </code_snippet>
        <finding>
            <severity>{{severity_level}}</severity>
            <line_number>{{line_number}}</line_number>
            <original_name>{{original_variable_name}}</original_name>
            <replacement_name>{{suggested_replacement_name}}</replacement_name>
            <reason>{{reason_for_replacement}}</reason>
        </finding>
    </example>
</examples>
"""
    user_message = code_content

    # Add debug logging
    logging.debug(f"System message: {system_message}")
    logging.debug(f"User message: {user_message}")

    # Use the OpenAI API to get the findings
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format=VariableNamingFindingList,
        )

        # Add debug logging
        logging.debug(f"LLM response: {completion}")

        message = completion.choices[0].message

        if message.parsed:
            findings = message.parsed
        elif message.refusal:
            logging.error(f"Model refused to analyze: {message.refusal}")
            return None
        else:
            logging.error("No parsed response received.")
            return None

    except Exception as e:
        logging.error(f"Error during LLM call: {str(e)}", exc_info=True)
        return None

    if not findings:
        logging.error("No findings returned.")
        return None

    return VariableNamingFindingList(findings=findings.findings)


async def refactor_poorly_named_resources(file_path: str) -> Optional[ResourceNamingFindingList]:
    """
    Analyzes the specified code file to identify poorly named Pulumi resource names and suggests replacements.

    Args:
        file_path (str): The path to the code file to analyze.

    Returns:
        Optional[ResourceNamingFindingList]: A list of resource naming findings or None if an error occurs.
    """
    # Ensure the file exists
    if not os.path.exists(file_path):
        logging.error(f"File '{file_path}' does not exist.")
        return None

    # Read the code content
    try:
        with open(file_path, 'r') as file:
            code_content = file.read()
    except Exception as e:
        logging.error(f"Failed to read the file: {str(e)}")
        return None

    # Construct the system and user messages
    system_message = f"""
You are analyzing code that includes Pulumi resource definitions to identify resources with names that are not clearly or well named. For each poorly named resource:
Be sure to look at every resource in the code and provide a finding for each one that is poorly named.

1. Assign a **severity level** from 1 (Trivial) to 5 (Critical) based on how problematic the resource name is.
2. Provide a **reason** for suggesting a replacement, choosing from predefined reasons.
3. Suggest a **replacement name** that follows best practices and naming conventions.

Provide the findings as a list of JSON objects with the following fields:

- `severity`: (int)
- `line_number`: (int)
- `original_name`: (str)
- `replacement_name`: (str)
- `reason`: (str)

Ensure that the `original_name` and `replacement_name` fields only contain the resource names, without any additional code or context.

Do not report resources that are well-named and do not require any changes.

{SEVERITY_CRITERIA}

{POSSIBLE_REASONS}

<examples>
    <!-- Specific Example -->
    <example>
        <code_snippet>
            cloud_trail_trail00skoutcloudtrail00p_ns4_e = pulumi_aws.cloudtrail.Trail(
                "CloudTrailTrail00skoutcloudtrail00pNS4E",
                cloud_watch_logs_group_arn="arn:aws:logs:us-east-1:123456789012:log-group:CloudTrail/test:*",
                # ...
                is_multi_region_trail=True,
                name="skoutcloudtrail",
                s3_bucket_name="skoutcloudtrail",
                # ...
            )
        </code_snippet>
        <finding>
            <severity>5</severity>
            <line_number>45</line_number>
            <original_name>CloudTrailTrail00skoutcloudtrail00pNS4E</original_name>
            <replacement_name>cloudtrail_trail_for_skout</replacement_name>
            <reason>Nonsensical or meaningless name</reason>
        </finding>
    </example>
    <!-- Templated Example -->
    <example>
        <code_snippet>
            {{original_resource_code}}
        </code_snippet>
        <finding>
            <severity>{{severity_level}}</severity>
            <line_number>{{line_number}}</line_number>
            <original_name>{{original_resource_name}}</original_name>
            <replacement_name>{{suggested_replacement_name}}</replacement_name>
            <reason>{{reason_for_replacement}}</reason>
        </finding>
    </example>
</examples>

**After suggesting a replacement, reevaluate the new resource name to ensure it does not itself require improvement. Refine the replacement name if necessary until it meets the criteria for a well-named resource.**
"""
    user_message = code_content

    # Add debug logging
    logging.debug(f"System message: {system_message}")
    logging.debug(f"User message: {user_message}")

    # Use the OpenAI API to get the findings
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format=ResourceNamingFindingList,
        )

        # Add debug logging
        logging.debug(f"LLM response: {completion}")

        message = completion.choices[0].message

        if message.parsed:
            findings = message.parsed
        elif message.refusal:
            logging.error(f"Model refused to analyze: {message.refusal}")
            return None
        else:
            logging.error("No parsed response received.")
            return None

    except Exception as e:
        logging.error(f"Error during LLM call: {str(e)}", exc_info=True)
        return None

    if not findings:
        logging.error("No findings returned.")
        return None

    return ResourceNamingFindingList(findings=findings.findings)


def perform_variable_refactoring(findings, file_path, persistent_file_path):
    logging.info(f"Starting variable refactoring for file: {file_path}")
    lock_file_path = os.path.join(scratch_pad_dir, "refactor.lock")

    # Wait until the lock file is deleted
    while os.path.exists(lock_file_path):
        logging.debug(f"Waiting for lock file {lock_file_path} to be deleted...")
        time.sleep(1)

    # Create the lock file
    logging.debug(f"Creating lock file at {lock_file_path}")
    with open(lock_file_path, "w") as file:
        file.write("")

    try:
        # Load the list of already refactored variables
        logging.debug(f"Loading refactored variables from {persistent_file_path}")
        if os.path.exists(persistent_file_path):
            with open(persistent_file_path, 'r') as f:
                refactored_variables = json.load(f)
        else:
            refactored_variables = {}

        # Read the source code
        with open(file_path, 'r') as file:
            source_code = file.read()

        # Initialize the Rope project
        project = Project(os.path.dirname(file_path))
        resource = libutils.path_to_resource(project, file_path)

        # Create a mapping from variable names to findings
        finding_dict = {finding.original_name: finding for finding in findings}

        # Get the list of target variable names
        target_variable_names = finding_dict.keys()

        # Parse the source code with ast
        parsed_ast = ast.parse(source_code)

        # Create and run the visitor
        visitor = VariableDefVisitor(target_variable_names)
        visitor.visit(parsed_ast)

        if not visitor.found_variables:
            logging.error("No variables found in the source code for refactoring.")
            return

        for variable_info in visitor.found_variables:
            variable_name = variable_info['name']
            node = variable_info['node']
            lineno = variable_info['lineno']
            col_offset = variable_info['col_offset']
            finding = finding_dict[variable_name]
            old_name = finding.original_name
            new_name = finding.replacement_name
            logging.info(f"Processing variable '{old_name}' at line {lineno}, column {col_offset}")

            # Check if already refactored
            if old_name in refactored_variables:
                logging.info(f"Variable '{old_name}' has already been refactored; skipping.")
                continue

            # Skip if the old variable name is not a valid identifier
            if not identifier_regex.match(old_name):
                logging.warning(f"Variable name '{old_name}' is not a valid Python identifier; skipping.")
                continue

            # Skip if the new variable name is not a valid identifier
            if not identifier_regex.match(new_name):
                logging.warning(f"Replacement name '{new_name}' is not a valid Python identifier; skipping.")
                continue

            try:
                # Calculate the offset
                offset = _get_offset_from_lineno_col(source_code, lineno, col_offset, variable_name)
                # Initialize the Rename refactoring
                rename = Rename(project, resource, offset)
                changes = rename.get_changes(new_name)
                project.do(changes)
                project.sync()
                logging.info(f"Successfully refactored variable '{old_name}' to '{new_name}' at line {lineno} and column {col_offset} using Rope.")

                # Update refactored variables list
                refactored_variables[old_name] = new_name

            except (BadIdentifierError, SyntaxError) as e:
                logging.warning(f"Skipping variable '{old_name}' due to an error: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Error refactoring variable '{old_name}' to '{new_name}' at line {lineno} and column {col_offset}: {str(e)}", exc_info=True)
                continue

        # Save the updated refactored variables
        logging.debug(f"Saving refactored variables to {persistent_file_path}")
        with open(persistent_file_path, 'w') as f:
            json.dump(refactored_variables, f, indent=4)

    finally:
        # Close the project
        project.close()
        # Delete the lock file
        logging.debug(f"Deleting lock file at {lock_file_path}")
        os.remove(lock_file_path)


def _get_offset_from_lineno_col(source_code, lineno, col_offset, variable_name):
    lines = source_code.splitlines(keepends=True)
    if lineno - 1 >= len(lines):
        raise ValueError(f"Line number {lineno} is out of range.")
    line = lines[lineno - 1]

    # Use regex to find the exact position of the variable name in the line
    pattern = r'\b' + re.escape(variable_name) + r'\b'
    matches = list(re.finditer(pattern, line))

    if not matches:
        logging.warning(f"Variable name '{variable_name}' not found on line {lineno}.")
        raise ValueError(f"Variable name '{variable_name}' not found on line {lineno}.")
    
    # Assume the first match is the variable definition
    idx = matches[0].start()

    offset = sum(len(lines[i]) for i in range(lineno - 1)) + idx
    return offset


class VariableDefVisitor(ast.NodeVisitor):
    def __init__(self, target_variables):
        self.target_variables = set(target_variables)
        self.found_variables = []  # List of dicts with 'name', 'node', 'lineno', 'col_offset'

    def visit_Assign(self, node):
        for target in node.targets:
            self.process_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self.process_target(node.target)
        self.generic_visit(node)

    def process_target(self, target):
        if isinstance(target, ast.Name) and target.id in self.target_variables:
            self.found_variables.append({
                'name': target.id,
                'node': target,
                'lineno': target.lineno,
                'col_offset': target.col_offset
            })
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self.process_target(elt)


def perform_resource_refactoring(findings, file_path, persistent_file_path):
    logging.info(f"Starting resource refactoring for file: {file_path}")
    lock_file_path = os.path.join(scratch_pad_dir, "refactor.lock")

    # Wait until the lock file is deleted
    while os.path.exists(lock_file_path):
        logging.debug(f"Waiting for lock file {lock_file_path} to be deleted...")
        time.sleep(1)

    # Create the lock file
    logging.debug(f"Creating lock file at {lock_file_path}")
    with open(lock_file_path, "w") as file:
        file.write("")

    try:
        # Load the list of already refactored strings
        logging.debug(f"Loading refactored strings from {persistent_file_path}")
        if os.path.exists(persistent_file_path):
            with open(persistent_file_path, 'r') as f:
                refactored_strings = json.load(f)
        else:
            refactored_strings = {}

        # Read the source code
        with open(file_path, 'r') as file:
            source_code = file.read()

        # Iterate over resource findings
        for finding in findings:
            old_string = finding.original_name
            new_string = finding.replacement_name
            logging.debug(f"Processing string '{old_string}'")

            # Check if already refactored
            if old_string in refactored_strings:
                logging.info(f"String '{old_string}' has already been refactored; skipping.")
                continue

            # Escape special regex characters in old_string
            escaped_old_string = re.escape(old_string)

            # Replace the old string with the new one using regex to match exact words
            
            def create_double_quoted_pattern(escaped_string):
                return f'"{escaped_string}"'
            
            def create_single_quoted_pattern(escaped_string):
                return f"'{escaped_string}'"

            old_pattern__double_quoted = create_double_quoted_pattern(escaped_old_string)
            new_pattern__double_quoted = create_double_quoted_pattern(new_string)
            old_pattern__single_quoted = create_single_quoted_pattern(escaped_old_string)
            new_pattern__single_quoted = create_single_quoted_pattern(new_string)

            num_replacements = 0
            source_code, num_replacements_result1 = re.subn(
                old_pattern__double_quoted,
                new_pattern__double_quoted,
                source_code,
            )
            source_code, num_replacements_result2 = re.subn(
                old_pattern__single_quoted,
                new_pattern__single_quoted,
                source_code,
            )

            num_replacements += num_replacements_result1 + num_replacements_result2

            if num_replacements > 0:
                logging.info(f"Refactored '{old_string}' to '{new_string}' in {num_replacements} places.")
                refactored_strings[old_string] = new_string
            else:
                logging.warning(f"No occurrences of '{old_string}' found.")

        # Write the modified source code back to the file
        with open(file_path, 'w') as file:
            file.write(source_code)

        # Save the updated refactored strings
        logging.debug(f"Saving refactored strings to {persistent_file_path}")
        with open(persistent_file_path, 'w') as f:
            json.dump(refactored_strings, f, indent=4)

    finally:
        # Delete the lock file
        logging.debug(f"Deleting lock file at {lock_file_path}")
        os.remove(lock_file_path)


async def refactor(file_path: str) -> dict:
    logging.debug(f"Starting refactoring for file: {file_path}")
    """
    Wraps the refactoring functions for variables and resources, consolidates their findings,
    and writes the results to a single file in the scratchpad directory.

    Args:
        file_path (str): The path to the code file to analyze and refactor.

    Returns:
        dict: A dictionary indicating success or failure.
    """

    # Run the variable and resource findings in parallel
    variable_findings_task = asyncio.create_task(refactor_poorly_named_variables(file_path))
    resource_findings_task = asyncio.create_task(refactor_poorly_named_resources(file_path))

    variable_findings = await variable_findings_task
    resource_findings = await resource_findings_task

    # Check if any findings are None
    if variable_findings is None:
        logging.error(f"Failed to analyze variables for file: {file_path}")
        return {"status": "error", "message": "Failed to analyze variables."}
    if resource_findings is None:
        logging.error(f"Failed to analyze resources for file: {file_path}")
        return {"status": "error", "message": "Failed to analyze resources."}

    logging.debug(f"Variable findings: {variable_findings}")
    logging.debug(f"Resource findings: {resource_findings}")

    # Create a RefactoringFindings instance
    findings = RefactoringFindings(
        file=file_path,
        language="python",
        variable_findings=variable_findings,
        resource_findings=resource_findings,
    )

    logging.debug(f"Refactoring findings: {findings}")

    # Write the findings to a results file
    os.makedirs(scratch_pad_dir, exist_ok=True)
    results_file_path = os.path.join(scratch_pad_dir, "refactoring_findings.json")

    logging.debug(f"Writing results to file: {results_file_path}")

    try:
        with open(results_file_path, 'w') as f:
            f.write(findings.model_dump_json(indent=4))
    except Exception as e:
        logging.error(f"Failed to write results file: {str(e)}")
        return {"status": "error", "message": f"Failed to write results file: {str(e)}"}

    # Load findings from the results file
    with open(results_file_path, 'r') as f:
        findings_data = json.load(f)

    variable_findings = [VariableNamingFinding(**finding) for finding in findings_data['variable_findings']['findings']]
    resource_findings = [ResourceNamingFinding(**finding) for finding in findings_data['resource_findings']['findings']]

    logging.debug(f"Loaded variable findings: {variable_findings}")
    logging.debug(f"Loaded resource findings: {resource_findings}")

    # Set paths for persistent files
    variable_persistent_file = os.path.join(scratch_pad_dir, "refactored_variables.json")
    resource_persistent_file = os.path.join(scratch_pad_dir, "refactored_strings.json")

    logging.debug(f"Variable persistent file: {variable_persistent_file}")
    logging.debug(f"Resource persistent file: {resource_persistent_file}")

    # Perform refactoring
    perform_variable_refactoring(variable_findings, file_path, variable_persistent_file)
    # perform_resource_refactoring(resource_findings, file_path, resource_persistent_file)

    logging.info(f"Refactoring completed for file: {file_path}")

    return {
        "status": "success",
        "message": "Refactoring completed and findings written to scratchpad.",
        "results_file": results_file_path,
    }
