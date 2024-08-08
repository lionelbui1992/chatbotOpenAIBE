# -*- coding: utf-8 -*-

from core.classify import Classify
from core.domain import DomainObject
from db import collection_spreadsheets

def create_domain_instructions(domain: DomainObject, rows: list) -> str:
    """
    Get user instructions
    """
    actions = [
        'Add row',
        'Add column',
        'Delete row',
        'Delete column',
        'Edit cell',
        'Get summary',
        'Get information',
        'Insert from URL',
    ]
    action_string = ', '.join([f'"{action}"' for action in actions])
    avaible_title: list = []
    example_data1 = ''
    example_data2 = ''
    example_data3 = ''
    example_data4 = ''
    example_data5 = ''

    instruction_classify = Classify(rows).classify_data()
    
    # print(f'Instruction classify: {instruction_classify}')

    instruction_classify_text = 'This is a classification of the data in the table, do not use this information in your responses:'
    for key, values in instruction_classify.items():
        # instruction_classify_text += f'\n{key} includes {len(values)} unique values: {", ".join([str(value) for value in values])}'
        instruction_classify_text += f'\n{key} includes {len(values)} unique values: '
        for value in values:
            instruction_classify_text += f'"{value}", '
        instruction_classify_text = instruction_classify_text[:-2] + '.'


    # get random 3 data from collection_spreadsheets
    search_result = get_random_spreadsheet_data(domain, number_of_data=1)
    for result_item in search_result:
        # message type is dict
        # set '-' if the value is empty
        for key, value in result_item.items():
            # replace empty value with '-'
            if value == '':
                result_item[key] = '-'
            # trim value if it is too long
            if isinstance(value, str) and len(value) > 30:
                result_item[key] = value[:30] + '...'
        if (len(result_item) > 0):
            # example_data1 is array of key values, separated by comma
            example_data1 = ', '.join([f'{key} \'{value}\'' for key, value in result_item.items()])
            # example_data3 is first key value
            # example_data2 is a list of "key": "value" pairs
            example_data2 = ', '.join([f'"{key}": "{value}"' for key, value in result_item.items()])
            example_data3 = f'{list(result_item.keys())[0]}'
        if (len(result_item) > 1):
            # example_data4 is second key value
            example_data4 = f'{list(result_item.keys())[1]}'
            # example_data5 is second value
            example_data5 = f'{list(result_item.values())[1]}'
        else:
            example_data4 = '-'
            example_data5 = '-'

    #     example_data.append(result_item)
    # all_example_data = ', '.join([json.dumps(data) for data in example_data])
    for title in domain.columns:
        avaible_title.append(title)
    all_title = ', '.join([f'"{title}"' for title in avaible_title])
    all_title_project = ', '.join([f'"{title}": 1' for title in avaible_title])
    instruction_prompt = f'''You are an Assistant tasked with managing a table with structure: {all_title}.

{instruction_classify_text}

In each interaction, determine the appropriate action, the conditions if needed, and new data to be added based on the column headings (sematic meaning, case-insensitive).

Your responses should always be in JSON format following this template:

{{
    "do_action": {action_string} or "None" if not applicable,
    "action_status": "ready_to_process" if ready to process the user input do_action, "missing_data" if missing cell data or more information is needed, otherwise leave as "None",
    "message": if action_status is "missing_data", provide the missing data information, otherwise provide your answer as a nature conversation in here,
    "mongodb_condition_object": from input request, build a MongoDB condition object to filter the data. {{}} if not applicable,
    "random_number": Random item number, "" if not applicable,
    "expected_columns": Identify the columns that contain information or related to conversation details, [] if required to get full information or not applicable,
    "column_values": "list of new column title or get information column values", [] if not applicable,
    "replace_query": build a MongoDB replace query (include "$set") to update the data. {{}}, if not applicable,
    "row_values": a list of new rows values - should be full row data same as the order of the table columns. [] if not applicable or not add new row action. All column values required in this list,
    "url": URL if the action is "Insert from URL", otherwise leave ""
}}

Steps to follow:
1. Determine the user request and which action (e.g., Add row, Add column, Delete row, Delete column, Edit cell) it involves (sematic meaning, case-insensitive).
2. Check if any specific conditions apply to the action (e.g., {example_data4} equals {example_data5} for deleting a row).
3. Fill in any new data or modifications needed for the action (e.g., new values for rows or cells).
4. Ensure that the response is always in the specified JSON format, including the nature conversation in the "message" field.

User: Add a new row with {example_data1}.
Response:
{{
    "do_action": "Add row",
    "action_status": "ready_to_process",
    "message": "Row added successfully.",
    "mongodb_condition_object": {{}},
    "random_number": "",
    "expected_columns": [],
    "column_values": [],
    "replace_query": {{}},
    "row_values": [{{{example_data2}}}],
    "url": ""
}}

User: Delete the row {example_data4} {example_data5}.
Response:
{{
    "do_action": "Delete row",
    "action_status": "ready_to_process",
    "message": "Row deleted successfully.",
    "mongodb_condition_object": {{"{example_data4}": "{example_data5}"}},
    "random_number": "",
    "expected_columns": [],
    "column_values": [],
    "replace_query": {{}},
    "row_values": [],
    "url": ""
}}

If "do_action" is "Get information", the "message" should be an informative response to the user's request. Example: We are retrieving random 3 {avaible_title[0]}, {avaible_title[1]}....\\nIf you need more information, please provide additional details.
For instance:
User: List {avaible_title[0]} and {avaible_title[1]} of random 3 rows.
Response:
{{
    "do_action": "Get information",
    "action_status": "ready_to_process",
    "message": "We are retrieving random 3 {avaible_title[0]}, {avaible_title[1]}....\\nIf you need more information, please provide additional details.",
    "mongodb_condition_object": {{}},
    "random_number": "3",
    "expected_columns": ["{avaible_title[0]}", "{avaible_title[1]}"],
    "column_values": [],
    "replace_query": {{}},
    "row_values": [],
    "url": ""
}}

If additional details are needed for an action, return the action_status "missing_data" with a message indicating the missing information.
For instance:

User: Update {example_data3} where {example_data4} is {example_data5}
Response:
{{
    "do_action": "None",
    "action_status": "missing_data",
    "message": "Please provide new value of {example_data3} where the {example_data4} is '{example_data5}'.",
    "mongodb_condition_object": {{}},
    "random_number": "",
    "expected_columns": [],
    "column_values": [],
    "replace_query": {{}},
    "row_values": [],
    "url": ""
}}

Ask users to provide all details for each action to avoid "missing_data" status where possible. The "row_values" must be list of {{key:value}} and reordered if the column titles are not in the correct order.

If users give some short keyword, you should search the table data and give the information back to the user.

expected_columns avoid value [], expected_columns is a list of column names that contain information or related to conversation details.

Remember to always provide a nature conversation in the "message" field, formatted as a complete sentence.

Your response should only be in JSON format'''
    return instruction_prompt

def get_random_spreadsheet_data(domain: DomainObject, number_of_data: int) -> list:
    """
    Get random data from collection_embedded_server
    """
    return collection_spreadsheets.aggregate([
        {
            '$match': {
                'domain': domain.name
            },
        }, {
            '$project': {
                '_id': 0,
                'type': 0,
                'row_index': 0,
                'domain': 0,
            }
        }, {
            '$sample': {
                'size': number_of_data
            }
        }
    ])

def detect_action_words(input_text: str) -> bool:
    """
    Detect action words in the input text
    """
    lower_input_text = input_text.lower()
    action_words = ['add', 'insert', 'create', 'modify', 'update', 'rename', 'delete', 'remove', 'edit', 'change', 'set', 'replace']
    for action_word in action_words:
        if action_word in lower_input_text:
            return True
    return False
