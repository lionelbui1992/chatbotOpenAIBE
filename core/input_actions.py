from core.domain import DomainObject
from core.openai import create_completion
from db import collection_spreadsheets

def create_domain_instructions(domain: DomainObject) -> str:
    """
    Get user instructions
    """
    avaible_title: list = []
    example_data1 = ''
    example_data2 = ''
    example_data3 = ''
    example_data4 = ''
    example_data5 = ''


    # get random 3 data from collection_spreadsheets
    search_result = get_random_spreadsheet_data(domain, number_of_data=1)
    for result_item in search_result:
        # message type is dict
        # set '-' if the value is empty
        for key, value in result_item.items():
            if value == '':
                result_item[key] = '-'
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
    instruction_prompt = f'''You are tasked with managing a table with the following structure: {all_title}.

In each interaction, determine the appropriate action, the conditions if needed, and new data to be added based on the column headings (sematic meaning, case-insensitive).

Your responses should always be in JSON format following this template:

{{
    "status": "skip" if conversation is not applicable, "ready_to_process" if ready to process the user input action, "missing_data" if add new widh missing cell data or more information is needed.
    "message": if status is "missing_data", provide the missing data information, otherwise leave your chat response,
    "action": "Add row", "Add column", "Delete row", "Delete column", "Edit cell" or "None", "Get summary", "Get information" if not applicable,
    "conditions": [
        {{
            "column_title": "column title value", "" if not applicable,
            "condition": "equals", "not equals", "greater than", "less than", "greater than or equal to", "less than or equal to", "contains", "not contains", "starts with", "ends with", "" if not applicable,
            "value": "value to compare to", "" if not applicable
        }}
    ] or [] if not applicable,
    "column_title": "column title value", [] if not applicable,
    "value_to_replace": "row new value", "" if not applicable,
    "values": a list of rows values. [] if not applicable, value should be full row data in the order of the table columns. All column values required in this list.
}}

Steps to follow:
1. Determine the user request and which action (e.g., Add row, Add column, Delete row, Delete column, Edit cell) it involves (sematic meaning, case-insensitive).
2. Check if any specific conditions apply to the action (e.g., {example_data4} equals {example_data4} for deleting a row).
3. Fill in any new data or modifications needed for the action (e.g., new values for rows or cells).
4. Ensure that the response is always in the specified JSON format.

User: "Add a new row with {example_data1}"
Response:
{{
    "status": "ready_to_process",
    "message": "",
    "action": "Add row",
    "conditions": [],
    "column_title": [],
    "value_to_replace": "",
    "values": [{{{example_data2}}}]
}}

User: "Delete the row with {example_data4} {example_data5}"
Response:
{{
    "status": "ready_to_process",
    "message": "",
    "action": "Delete row",
    "conditions": [
        {{
            "column_title": "{example_data4}",
            "condition": "equals",
            "value": "{example_data5}"
        }}
    ],
    "column_title": [],
    "value_to_replace": "",
    "values": []
}}

If additional details are needed for an action, return the status "missing_data" with a message indicating the missing information.
For instance:

User: "Update the {example_data3} for the row where {example_data4} is '{example_data5}'"
Response:
{{
    "status": "missing_data",
    "message": "Please provide the {example_data3} of the row where the {example_data4} value is '{example_data5}'.",
    "action": "None",
    "conditions": [],
    "column_title": [],
    "value_to_replace": "",
    "values": []
}}

Ask users to provide all details for each action to avoid "missing_data" status where possible. The "values" must be reordered if the column titles are not in the correct order.

Your response should only be in JSON format'''
    return instruction_prompt

def get_analysis_input_action(messages: list) -> dict:
    """
    Given an input text, determine the appropriate action
    Return data will be: {action, title, old_value, new_value} as JSON format
    """
    completion = create_completion(messages=messages)
    message = completion.choices[0].message.content
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('Action analysis: ', message)
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    return completion

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

