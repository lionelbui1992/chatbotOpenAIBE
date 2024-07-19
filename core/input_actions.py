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
    aggregate_result = collection_attribute.aggregate([
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
    for message in aggregate_result:
        avaible_title.append(message['title'])
    
    all_title = ', '.join([f'"{title}"' for title in avaible_title])
    print('||||||||||||||||||||All title: ', all_title)
    # print('||||||||||||||||||||All title',)

    # get random 3 data from collection_embedded_server
    aggregate_result = collection_embedded_server.aggregate([
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
                'size': 3
            }
        }
    ])

    for message in aggregate_result:
        # message type is dict
        example_data.append(message)
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
        model="gpt-3.5-turbo",
        messages= var_messages
    )
    message = completion.choices[0].message.content
    print('::::::::::::::::::::::::::::::::::::::::::::::')
    print('prompt: ', var_messages)
    print('::::::::::::::::::::::::::::::::::::::::::::::')
    
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
