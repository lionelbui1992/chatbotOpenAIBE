from pymongo import MongoClient
import torch

from transformers import BertTokenizer, BertModel
import torch


client = MongoClient('mongodb+srv://lionelbui:pEciuiTKR28LKOMs@cluster0.hm7buca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['sample_mflix']
collection_cell_words = db['cell_words'] # _id, domain, row_index, column_title, text, words: [{word, vector}]

model_name="bert-base-uncased"

tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

def words_to_vectors(words):
    if isinstance(words, str):
        words = [words]
    tokens = tokenizer(words, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**tokens)
        vectors = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return vectors

# search_vector = words_to_vectors("iphone")
# print(search_vector.tolist())
# for doc in collection_cell_words.aggregate([
#     {
#         "$vectorSearch": {
#             "index": "vector_index",
#             "path": "vector",
#             "queryVector": search_vector.tolist(),
#             "numCandidates": 150,
#             "limit": 10,
#         }
#     },
#     {
#         '$match': {
#             'domain': 'domain-5'
#         }
#     },
#     {
#         '$project': {
#             '_id': 0,
#             'row_index': 1,
#             # 'column_title': 1,
#             'text': 1,
#             'word': 1,
#             'score': {
#                 '$meta': 'vectorSearchScore'
#             }
#         }
#     }
# ]):
#     print(doc)

# search data
# for doc in collection_cell_words.aggregate([
#     {
#         "$search": {
#             "index": "default",
#             "text": {
#                 "query": "ipon",
#                 "path": ["text"],
#                 "fuzzy": {
#                     "maxEdits": 2,
#                     "prefixLength": 0,
#                     "maxExpansions": 50
#                 }
#             }
#         },
#     },
#     {
#         '$match': {
#             'domain': 'domain-5'
#         }
#     },
#     {
#         '$limit': 10
#     },
#     {
#         '$project': {
#             '_id': 0,
#             'row_index': 1,
#             'text': 1,
#             'word': 1,
#             'score': {
#                 '$meta': 'searchScore'
#             }
#         }
#     }
# ]):
#     print(doc)

def get_cell_info(domain: str, input_text: str) -> list:
    """Search cell information from MongoDB"""

    return list(collection_cell_words.aggregate([
        {
            "$search": {
                "index": "default",
                "text": {
                    "query": input_text,
                    "path": ["text"],
                    "fuzzy": {
                        "maxEdits": 2,
                        "prefixLength": 0,
                        "maxExpansions": 50
                    }
                }
            },
        },
        {
            '$match': {
                'domain': domain
            }
        },
        {
            '$limit': 10
        },
        {
            '$project': {
                '_id': 0,
                'row_index': 1,
                'column_title': 1,
                'text': 1,
                'word': 1,
                'score': {
                    '$meta': 'searchScore'
                }
            }
        }
    ]))


def get_best_match(domain: str, input_text: str, limit=3) -> dict | None:
    """Get the best match from the cell words"""

    result = get_cell_info(domain, input_text)
    if len(result) < 1:
        return None
    # get list of column_title, if row_index is the same get the highest score
    best_match = dict()
    for item in result:
        if item['column_title'] in best_match:
            if item['score'] > best_match[item['column_title']]['score']:
                best_match[item['column_title']] = item
        else:
            best_match[item['column_title']] = item
    # sort by score
    best_match = sorted(best_match.values(), key=lambda x: x['score'], reverse=True)
    return best_match[:limit] if len(best_match) > 0 else None

domain = 'domain-5'
input_txt = ['iphone', 'iphone 12', 'ipon', 'apple', 'xiaomi', 'samsung', 'huawei', 'oneplus']
for txt in input_txt:
    print(f"=============================='{txt}'==============================")
    print('\n'.join([f'{result["score"]}\t\t||\t{result["text"]}' for result in get_best_match(domain, txt)]))
    print(f"------------------------------'{txt}'------------------------------")
    print(f"-------------------------------------------------------------------")
    print(f"-------------------------------------------------------------------")
    print(f"-------------------------------------------------------------------")
