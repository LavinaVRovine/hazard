import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sqlalchemy import create_engine
from LOL_formatter import Formatter
from sklearn.externals import joblib
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

class My_predictor:

    def __init__(self, db_location):
        df = self.load_train_df(db_location)
        self.train_df = self.format_train_df(df)
        self.scaler = self.get_scaler()

    def load_train_df(self, db_location):
        engine = create_engine(db_location,
                               echo=False)
        return pd.read_sql("SELECT * FROM basic_predictions", engine)

    def format_train_df(self, train_dataset):
        formatter = Formatter(train_dataset)
        df = formatter.main_reformat()
        df = formatter.drop_for_predict(df)
        return df

    def get_scaler(self):
        standard_scaler = preprocessing.StandardScaler()
        df = self.train_df.copy()
        # asi musim loopvat pres kazdy
        x = df.values  # returns a numpy array
        standard_scaler.fit(x)
        return standard_scaler

    def training(self):

        df = self.train_df

        y = df.pop("main_team_won")
        # asi musim loopvat pres kazdy
        x = df.values  # returns a numpy array
        #standard_scaler = preprocessing.StandardScaler()
        #x_scaled = standard_scaler.fit_transform(x)
        #x_scaled = self.scaler.transform(x)
        #df_scaler = pd.DataFrame(x_scaled)

        X_train, X_test, y_train, y_test = train_test_split(df, y,
                                                            test_size=0.2)

        model = LogisticRegression()
        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)
        print(f"yay its working with {score}")
        #self.save_model(model)


    def load_saved_model(self):
        return joblib.load('data/filename.joblib')


    def save_model(self, classifier):
        joblib.dump(classifier, 'data/filename.joblib')
        return True

    def train_on_whole(self):
        pass

    def format_one_prediction(self, classes, probabilities):
        return {classes[0]: probabilities[0][0], classes[1]: probabilities[0][1]}


    def predict_one_match(self, row):
        clf = self.load_saved_model()
        labels = clf.classes_
        training_cols =  list(self.train_df.columns)
        training_cols.remove("main_team_won")
        row = row[training_cols]

        probabilities = clf.predict_proba(row)
        return self.format_one_prediction(labels, probabilities)

def try_mxnet():
    from mxnet import nd, autograd, gluon
    import mxnet as mx
    from mxnet.gluon import nn

    pred = My_predictor()
    df = pred.format_train_df(pred.load_train_df())
    y = df.pop("main_team_won")
    X = df.copy()
    category_count = 2
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
    net = gluon.nn.Sequential()
    with net.name_scope():
       net.add(gluon.nn.Dense(128, activation="relu"))
       net.add(gluon.nn.Dense(64, activation="relu"))
       net.add( nn.Dense(category_count))
   # net = nn.Dense(category_count)
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

# used for training new models
if __name__ == "__main__":
    #try_mxnet()


    pred = My_predictor()

    df = pred.load_train_df()
    formatter = Formatter(df)
    df = formatter.main_reformat()
    #y = df.pop("main_team_won")
    #X = df.copy()

    #category_count = 2

    #X_train, X_test, y_train, y_test = train_test_split(df, y,
     #                                                   test_size=0.2)

    df = df.reindex(
        columns=(['main_team_won'] + list([a for a in df.columns if a != 'main_team_won'])))
    pass


