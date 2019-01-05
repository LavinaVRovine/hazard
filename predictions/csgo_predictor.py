import pandas as pd
from sqlalchemy import create_engine
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)
from config import DATABASE_URI
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)

print("reading csho stats, which takes a while")
df = pd.read_sql_table("brutal_match_stats", con=ENGINE).drop_duplicates()

# super quick fix for imbalanced dataset; drop
drop_frac = (len(df.t1_winner[df.t1_winner == True]) - len(df.t1_winner[df.t1_winner == False]))/len(df.t1_winner[df.t1_winner == True])
df = df.drop(df.query('t1_winner == True').sample(frac=drop_frac).index)

y = df.pop("t1_winner")
df.fillna(0, inplace=True)
scaler = StandardScaler()

df.drop(["t1_id", "t2_id", "year", "match_id"], axis=1, inplace=True)
df.drop(["kast", "c_kast", "kd_diff", "c_kd_diff", "fk_diff", "c_fk_diff"], axis=1, inplace=True)
#df = scaler.fit_transform(df)


# X_train, X_test, y_train, y_test = train_test_split(df,y)
#
# model = LogisticRegression()
# model.fit(X_train,y_train)
# print(model.score(X_test, y_test))
#
# model = LogisticRegression(C=0.5)
# model.fit(X_train,y_train)
# print(model.score(X_test, y_test))
# model = LogisticRegression(C=1.5)
# model.fit(X_train,y_train)
# print(model.score(X_test, y_test))
#
# exit()

from mxnet import nd, autograd, gluon
import mxnet as mx
from mxnet.gluon import nn


X = df.copy()
# zda se, ze tohle nefunguje, jelikoz jsou to pandas objekty,
# pxnet pracuje jen s numpy


sample_count = len(X)
train_count = round(sample_count * 0.8)
valid_count = sample_count - train_count
feature_count = len(list(X.columns))
category_count = 2

X = X.values
y = y.values

X = nd.array(X)
y = nd.array(y)

X_train = mx.nd.crop(X, begin=(0, 0), end=(train_count, feature_count - 1))
X_test= mx.nd.crop(X, begin=(train_count, 0),
                     end=(sample_count, feature_count - 1))
y_train = y[0:train_count]
y_test = y[train_count:sample_count]


batch_size = 128
train = mx.gluon.data.DataLoader(
    mx.gluon.data.ArrayDataset(X_train, y_train),
    batch_size=batch_size, shuffle=True)
test = mx.gluon.data.DataLoader(mx.gluon.data.ArrayDataset(X_test, y_test),
                                batch_size=batch_size, shuffle=False)

net = mx.gluon.nn.Sequential()
# with net.name_scope():
#     net.add(gluon.nn.Embedding(30, 10))
#     net.add(gluon.rnn.LSTM(20))
#     net.add(gluon.nn.Dense(category_count, flatten=False))
#  net.initialize()
#
#
#
with net.name_scope():
    net.add(gluon.nn.Dense(256, activation="tanh"))
    net.add(gluon.nn.Dense(256, activation="relu"))
    net.add( nn.Dense(category_count))
# # net = nn.Dense(category_count)
net.collect_params().initialize(mx.init.Normal())
softmax = gluon.loss.SoftmaxCrossEntropyLoss()
trainer = gluon.Trainer(net.collect_params(), "sgd", {"learning_rate": 0.1})

epochs = 1000


def evaluate_accuracy(data_iterator, net):
    acc = mx.metric.Accuracy()
    for i, (data, label) in enumerate(data_iterator):
        # data = data.reshape((-1, 784))
        output = net(data)
        predictions = nd.argmax(output, axis=1)
        acc.update(preds=predictions, labels=label)
    return acc.get()[1]

for epoch in range(epochs):
    total_loss = 0
    for data, label in train:
        with autograd.record():
            output = net(data)
            loss = softmax(output, label)
        loss.backward()
        trainer.step(data.shape[0])
        total_loss += nd.sum(loss).asscalar()
    train_acc = evaluate_accuracy(train, net)
    test_acc = evaluate_accuracy(test, net)
    print(
        f"so in epoch {epoch} we have loss: {total_loss/60000} with train_acc {train_acc} and test acc {test_acc}")



