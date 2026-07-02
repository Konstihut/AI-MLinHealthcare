import pandas as pd
import numpy as np

from pyjedai.datamodel import Data
from pyjedai.block_building import StandardBlocking
from pyjedai.block_cleaning import BlockPurging, BlockFiltering
from pyjedai.matching import EntityMatching
from pyjedai.clustering import ConnectedComponentsClustering


TARGET_RECALL = 90.0 # In percent

# 1. Read data
d1 = pd.read_csv("data/sample/dirty_er_seed42_100/patients_dirty.csv", sep=',')
gt = pd.read_csv("data/sample/dirty_er_seed42_100/ground_truth.csv", sep=',')

d1 = d1.astype(object).where(pd.notnull(d1), "")

data = Data(
    dataset_1=d1,
    id_column_name_1='record_id',
    ground_truth=gt
)

# 2. Block Building
bb = StandardBlocking()
blocks = bb.build_blocks(
    data,
    attributes_1=["BIRTHDATE","DEATHDATE","PREFIX","FIRST",
                  "MIDDLE","LAST","SUFFIX","MAIDEN","MARITAL",
                  "RACE","ETHNICITY","GENDER","BIRTHPLACE",
                  "ADDRESS","CITY","STATE","COUNTY","ZIP"]
)

# 3. Block Cleaning-Filtering
bp = BlockPurging()
purged_blocks = bp.process(blocks, data, tqdm_disable=True)

bp.report()

bc = BlockFiltering(ratio=0.9)
filtered_blocks = bc.process(purged_blocks, data)


# 4. Entity Matching
em = EntityMatching(
    metric='jaccard',
    similarity_threshold=0.0
)
pairs_graph = em.predict(filtered_blocks, data)

# 5. Entity Clustering
#    Find SBW with highest precision above TARGET_RECALL
ec = ConnectedComponentsClustering()

results = []
for threshold in np.arange(0.0, 1.0, 0.01):
    clusters = ec.process(pairs_graph, data, similarity_threshold=threshold)
    metrics = ec.evaluate(clusters, verbose=False)
    results.append({
        "similarity_threshold": threshold,
        "precision": metrics['Precision %'],
        "recall": metrics['Recall %'],
        "f1": metrics['F1 %']
    })

results_df = pd.DataFrame(results)

qualifying = results_df[results_df["recall"] >= TARGET_RECALL]

if not qualifying.empty:
    best = qualifying.loc[qualifying["precision"].idxmax()]
    print(f"Highest Precision SBW with recall >= {TARGET_RECALL}%: \n{best}")
else:
    best = results_df.loc[results_df["recall"].idxmax()]
    print(f"No SBW with recall >= {TARGET_RECALL}% found! \nShowing SBW with highest recall: {best}")
