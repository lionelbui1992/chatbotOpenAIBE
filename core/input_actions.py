import json
from flask import current_app
from db import collection_embedded_server, collection_attribute

def get_analysis_input_action(input_text: str, domain: str):
    """
    Given an input text, determine the appropriate action
    Return data will be: {action, title, old_value, new_value} as JSON format
    """
    # get all availbe attributes in the database
    avaible_title: list = []
    example_data: list = []
    attribute_aggregate_result = collection_attribute.aggregate([
        {
            '$match': {
                'domain': domain
            }
        }, {
            '$project': {
                'title': 1, 
                'column_index': 1, 
                'domain': 1
            }
        }
    ])
    for message in attribute_aggregate_result:
        avaible_title.append(message['title'])
    
    all_title = ', '.join([f'"{title}"' for title in avaible_title])
    print('||||||||||||||||||||All title: ', all_title)
    # print('||||||||||||||||||||All title',)

    # get random 3 data from collection_embedded_server
    search_result = get_random_embedded_data(3)
    for result_item in search_result:
        # message type is dict
        example_data.append(result_item)
    all_example_data = ', '.join([json.dumps(data) for data in example_data])

    var_messages=[
        {
            "role": "user",
            "content":  f'''Given an input text, your task is to determine the appropriate action, column_title, action_conditions, old_value, new_value, and new_items based on the following criteria:

1. **Action**:
    - Action must be one of the following: "Add column", "Add row", "Modify", "Delete".
    - If no sematic matching action is found, set action to "None".

2. **Column Title**:
    - The column title (heading of the table) must be one of the following (case-insensitive): [{all_title}].
    - If action is "Add column", the column title should be the name of the new column.
    - If no sematic matching column title is found and the action is not "Add column", set column_title to "".

3. **Action Conditions**:
    - The action_conditions is list of column title (heading of the table).
    - The action_conditions item format is: "column_title": "conditions value".
    - If no matching conditions is found, set conditions to [].

4. **Old and New Values**:
    - If applicable based on the action, extract the old_value and new_value from the text. If not applicable, set them to "".

5. **New Items**:
    - If the action is "Add row", provide non-mentioned values with random values. Column titles should be: [{all_title}].
    - If the action is not "Add row", set new_items to [].

Here is the input text:
"""
{input_text}
"""

Your response should follow this JSON structure:
{{
    "action": "Modify",
    "conditions": [
        "column_title_1": "value_1",
        "column_title_2": "value_2",
    ],
    "column_title": "column_title_1",
    "old_value": "old_value",
    "new_value": "new_value",
    "new_items": []
}}
column_title_1, column_title_2, value_1, value_2, old_value, and new_value should be replaced with the appropriate values.
{{
    "action": "Add row",
    "conditions": [
        "column_title_1": "value_1",
        "column_title_2": "value_2",
    ],
    "column_title": "",
    "old_value": "",
    "new_value": "",
    "new_items": {all_example_data}
}}
new_items should be replaced with the appropriate values based on the action or random values as described by column titles.
**Guidelines**:
- If the action or column title can't be determined from the text, use "None".
- If the action conditions is not applicable, use [].
- If old_value or new_value are not applicable, use "".
- If action is "Add row" or "Add column", new_items should be a list of mentioned input texts or random values.
- If new_items are not applicable, use [].

Here are some example input texts to illustrate:
- "Update {avaible_title[0]} from old_value to new_value."
- "Modify {avaible_title[0]} from old_value to new_value."
- "Change {avaible_title[0]} from old_value to new_value."
- "Add row with random values."
- "Add row: {avaible_title[0]} = new_value."
- "Add some rows with random values."
- "Add column: column_title_1"
- "Add columns: column_title_1, column_title_2."
- "Delete column: column_title_1."
- "Delete columns: column_title_1, column_title_2."
- "Delete row: column_title_1 = value_1."
- "Delete rows: column_title_1 = value_1, column_title_2 = value_2."
- "Delete rows: column_title_1 is value_1 and column_title_2 is value_2."
old_value, new_value, value_1, value_2, column_title_1, column_title_2, and avaible_title should be replaced with the appropriate values.'''}
    ]
    completion = current_app.openAIClient.chat.completions.create(
        model="gpt-4o-mini",
        messages= var_messages
    )
    message = completion.choices[0].message.content
    # print('::::::::::::::::::::::::::::::::::::::::::::::')
    # print('prompt: ', var_messages)
    # print('::::::::::::::::::::::::::::::::::::::::::::::')
    
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('Action analysis: ', message)
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    return message

def get_analysis_input_action_v2(input_text: str, domain: str):
    """
    Given an input text, determine the appropriate action
    Return data will be: {action, title, old_value, new_value} as JSON format
    """
    avaible_title: list = []
    example_data1 = ''
    example_data2 = ''
    example_data3 = ''
    example_data4 = ''
    example_data5 = ''
    attribute_aggregate_result = collection_attribute.aggregate([
        {
            '$match': {
                'domain': domain
            }
        }, {
            '$project': {
                'title': 1, 
                'column_index': 1, 
                'domain': 1
            }
        }
    ])
    # get random 3 data from collection_embedded_server
    search_result = get_random_embedded_data(domain, 1)
    for result_item in search_result:
        # message type is dict
        # set '-' if the value is empty
        for key, value in result_item.items():
            if value == '':
                result_item[key] = '-'
        # example_data1 is array of key values, separated by comma
        example_data1 = ', '.join([f'{key} \'{value}\'' for key, value in result_item.items()])
        # example_data2 is array of values, separated by comma
        example_data2 = ', '.join([f'"{value}"' for value in result_item.values()])
        # example_data3 is first key value
        example_data3 = f'{list(result_item.keys())[0]}'
        # example_data4 is second key value
        example_data4 = f'{list(result_item.keys())[1]}'
        # example_data5 is second value
        example_data5 = f'{list(result_item.values())[1]}'

    #     example_data.append(result_item)
    # all_example_data = ', '.join([json.dumps(data) for data in example_data])
    for message in attribute_aggregate_result:
        avaible_title.append(message['title'])
    all_title = ', '.join([f'"{title}"' for title in avaible_title])
    prompt = f'''You are tasked with managing a table with the following structure: {all_title}.

In each interaction, determine the appropriate action, the conditions if needed, and new data to be added based on the column headings (sematic meaning).

Your responses should always be in JSON format following this template:

{{
    "status": "skip" if conversation is not applicable, "ready_to_process" if ready to process the user input action, "missing_data" if add new widh missing cell data or more information is needed.
    "message": if status is "missing_data", provide the missing data information, otherwise "",
    "action": "Add row", "Add column", "Delete row", "Delete column", "Edit cell" or "None" if not applicable,
    "conditions": [
        {{
            "column_title": "column title value", "" if not applicable,
            "condition": "equals", "not equals", "greater than", "less than", "greater than or equal to", "less than or equal to", "contains", "not contains", "starts with", "ends with", "" if not applicable,
            "value": "value to compare to", "" if not applicable
        }}
    ] or [] if not applicable,
    "column_title": "column title value", "" if not applicable,
    "new_column_title": "new column title value", "" if not applicable,
    "value_to_edit": "row old value", "" if not applicable,
    "value_to_replace": "row new value", "" if not applicable,
    "values": [] if not applicable, value should be full row data in the order of the table columns.
}}

Steps to follow:
1. Determine the user request and which action (e.g., Add row, Add column, Delete row, Delete column, Edit cell) it involves.
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
    "column_title": "",
    "new_column_title": "",
    "value_to_edit": "",
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
            "value": "{example_data4}"
        }}
    ],
    "column_title": "",
    "new_column_title": "",
    "value_to_edit": "",
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
    "column_title": "",
    "new_column_title": "",
    "value_to_edit": "",
    "value_to_replace": "",
    "values": []
}}

Ask users to provide all details for each action to avoid "missing_data" status where possible.

Your response should only be in JSON format.'''
    completion = current_app.openAIClient.chat.completions.create(
        model="gpt-4o-mini",
        messages= [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": input_text
            }
        ]
    )
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
    return message


def get_random_embedded_data(domain: str, number_of_data: int) -> list:
    """
    Get random data from collection_embedded_server
    """
    return collection_embedded_server.aggregate([
        {
            '$match': {
                'domain': domain
            },
        }, {
            '$project': {
                '_id': 0,
                'plot': 0,
                'plot_embedding': 0,
                'type': 0,
                'row_index': 0,
                'column_count': 0,
                'domain': 0,
                'title': 0,
                'header_column': 0
            }
        }, {
            '$sample': {
                'size': number_of_data
            }
        }
    ])