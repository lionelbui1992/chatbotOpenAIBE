import pandas as pd

class Classify:
    def __init__(self, data: list):
        self.data = data
        self.max_length = 500

    def classify_data(self):
        # Create DataFrame from data
        df = pd.DataFrame(self.data)

        # Display the initial data
        print("Initial data:")
        print(df)

        # Normalize data: remove unnecessary columns, duplicate data
        df = df.dropna(axis=1, how='all') # Remove columns with all empty values
        df = df.drop_duplicates() # Remove duplicate rows
        # remove column _id
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])

        # Classify and summarize data by title
        classified_data = {}
        for column in df.columns:
            value_counts = df[column].value_counts()
            classified_data[column] = value_counts

        # Refine data: remove empty, invalid, duplicate values; sort data in order
        for key in classified_data.keys():
            # Remove empty and invalid values
            classified_data[key] = classified_data[key][classified_data[key].index.notnull()]
            # Convert to a list of unique values and sort the values in order
            try:
                classified_data[key] = sorted([value for value in classified_data[key].index.tolist()])
            except Exception:
                classified_data[key] = [value for value in classified_data[key].index.tolist()]

        # Calculate the total length of the classified data string and remove the classified sets with a total length > 500 characters
        filtered_data = {}
        for key, values in classified_data.items():
            try:
                total_length = sum(len(value) for value in values)
            except Exception:
                total_length = 0
            if total_length <= self.max_length:
                filtered_data[key] = values

        # Display the classified and refined data
        print("\nClassified and refined data:")
        for key, values in filtered_data.items():
            print(f"\nTitle: {key}")
            print(f"Data size: {len(values)}")
            try:
                total_length = sum(len(value) for value in values)
            except Exception:
                total_length = 0
            print(f"Total data string length: {total_length}")
            for value in values:
                print(f" - {value}")



        return filtered_data

