import pandas as pd

def csv_to_structured_string(file_path):
    df = pd.read_csv(file_path)
    
    structured_string = ""
    
    columns = df.columns
    
    structured_string += " | ".join(columns) + "\n"
    structured_string += "-" * (len(structured_string) - 1) + "\n"
    
    for index, row in df.iterrows():
        row_string = " | ".join([str(item) for item in row])
        structured_string += row_string + "\n"
    
    return structured_string