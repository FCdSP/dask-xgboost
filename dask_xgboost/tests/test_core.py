import pandas as pd
import xgboost as xgb

import dask.dataframe as dd
from distributed import Client
from distributed.utils_test import gen_cluster, loop, cluster

import dask_xgboost as dxgb

df = pd.DataFrame({'x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                   'y': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]})
labels = pd.Series([1, 0, 1, 0, 1, 0, 1, 1, 1, 1])

param = {'max_depth': 2, 'eta': 1, 'silent': 1, 'objective': 'binary:logistic'}


@gen_cluster(client=True)
def test_dask(c, s, a, b):
    dtrain = xgb.DMatrix(df, label=labels)
    bst = xgb.train(param, dtrain)

    ddf = dd.from_pandas(df, npartitions=4)
    dlabels = dd.from_pandas(labels, npartitions=4)
    dbst = yield dxgb._train(c, param, ddf, dlabels)

    result = bst.predict(dtrain)
    dresult = dbst.predict(dtrain)

    correct = (result > 0.5) == labels
    dcorrect = (dresult > 0.5) == labels
    assert dcorrect.sum() >= correct.sum()


def test_synchronous_api(loop):
    dtrain = xgb.DMatrix(df, label=labels)
    bst = xgb.train(param, dtrain)

    ddf = dd.from_pandas(df, npartitions=4)
    dlabels = dd.from_pandas(labels, npartitions=4)

    with cluster() as (s, [a, b]):
        with Client(s['address'], loop=loop) as c:

            dbst = dxgb.train(c, param, ddf, dlabels)

            result = bst.predict(dtrain)
            dresult = dbst.predict(dtrain)

            correct = (result > 0.5) == labels
            dcorrect = (dresult > 0.5) == labels
            assert dcorrect.sum() >= correct.sum()
