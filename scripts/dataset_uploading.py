import os
import re
from .utils import *

def main(data_dir):
    datasets = []
    root, dirs, _ = next(os.walk(data_dir))

    for d in dirs:
        d_ = os.path.join(root, d)
        for f in os.listdir(d_):
            path = os.path.join(d_, f)
            f = re.sub('\.\w+$', '', f)
            dataset = collector.adapt_csv_dataset(path, dataset_name=f, task=d)
            collector.insert_data(dataset, dataset_name=f, task=d)
            datasets += [f]
    return datasets


main('D:\Datasets')