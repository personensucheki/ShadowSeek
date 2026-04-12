import json
import pandas as pd

def save_json(data, path):
    if not path:
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def save_csv(data, path):
    if not path:
        return
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
