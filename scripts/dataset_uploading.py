import os
import re
from .utils import *
dataset_langs = {
    "ASTD": ['Egyptian Arabic', 'arabic'],
    "ArSAS": ['Egyptian Arabic', 'North Levantine Arabic', 'South Levantine Arabic', 'arabic'],
    "MSTD": ['Moroccan Arabic', 'arabic'],
    "MARSA": ['Gulf Arabic', 'Omani Arabic', 'arabic'],
}


def main(data_dir, limit=-1):
    datasets = []
    root, dirs, _ = next(os.walk(data_dir))

    for d in dirs:
        d_ = os.path.join(root, d)
        for f in os.listdir(d_):
            path = os.path.join(d_, f)
            f = re.sub('\.\w+$', '', f)
            dataset = collector.adapt_csv_dataset(path, dataset_name=f, task=d)
            collector.insert_data(dataset[:limit], dataset_name=f, task=d)
            datasets += [f]
    return datasets