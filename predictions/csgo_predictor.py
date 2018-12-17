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

y = df.pop("t1_winner")
df.fillna(0, inplace=True)
scaler = StandardScaler()

df.drop(["t1_id", "t2_id", "year", "match_id"], axis=1, inplace=True)
df.drop(["kast", "c_kast", "kd_diff", "c_kd_diff", "fk_diff", "c_fk_diff"], axis=1, inplace=True)
#df = scaler.fit_transform(df)

X_train, X_test, y_train, y_test = train_test_split(df,y)


from mxnet import nd, autograd, gluon
import mxnet as mx
from mxnet.gluon import nn


X = df.copy()
# zda se, ze tohle nefunguje, jelikoz jsou to pandas objekty,
# pxnet pracuje jen s numpy
X_train, X_test, y_train, y_test = train_test_split(df, y,
                                                    test_size=0.2)

sample_count = len(X)  # 6036
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
    net.add(gluon.nn.Dense(128, activation="relu"))
    net.add(gluon.nn.Dense(64, activation="relu"))
    net.add( nn.Dense(category_count))
# # net = nn.Dense(category_count)
net.initialize(mx.init.Normal())
softmax = gluon.loss.SoftmaxCrossEntropyLoss()
trainer = gluon.Trainer(net.collect_params(), "sgd",
                        {"learning_rate": 0.001})

epochs = 1000
train_acc = mx.metric.Accuracy()
test_acc = mx.metric.Accuracy()

def evaluate_accuracy(data_iterator, net):
    acc = mx.metric.Accuracy()
    for i, (data, label) in enumerate(data_iterator):
        # data = data.reshape((-1, 784))
        output = net(data)
        predictions = nd.argmax(output, axis=1)
        acc.update(preds=predictions, labels=label)
    print(acc)
    return acc.get()[1]

for epoch in range(epochs):
    total_loss = 0
    for data, label in train:
        with autograd.record():
            output = net(data)
            loss = softmax(output, label)

        loss.backward()
        trainer.step(batch_size)
        total_loss += nd.sum(loss).asscalar()
    train_acc = evaluate_accuracy(train, net)
    test_acc = evaluate_accuracy(test, net)
    print(
        f"so in epoch {epoch} we have loss: {total_loss/60000} with train_acc {train_acc} and test acc {test_acc} ")

