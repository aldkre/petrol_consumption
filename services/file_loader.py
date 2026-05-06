import pandas as pd
import os

def load_csv(file, sample_data=False):
    if sample_data:
        services_dir = os.path.dirname(os.path.abspath(__file__))
        sample_path = os.path.join(services_dir, "sample.csv")
        df = pd.read_csv(sample_path, delimiter=";")
    else:
        df = pd.read_csv(file, sep=None, engine="python")

    df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
    return df
