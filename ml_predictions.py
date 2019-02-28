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
        # for DA
        self.df_for_da = None

        self.training_columns = None
        df = self.load_train_df(db_location)
        self.train_df = self.format_train_df(df)
        self.scaler = self.get_scaler()
        self.model = None


    def load_train_df(self, db_location):
        engine = create_engine(db_location,
                               echo=False)
        return pd.read_sql("SELECT * FROM basic_predictions", engine)

    def format_train_df(self, train_dataset):
        formatter = Formatter(train_dataset)
        df = formatter.main_reformat()
        df = formatter.drop_for_predict(df)
        # names NEEDED for DA
        self.df_for_da = df.copy()
        df.drop(["name", "c_name"], axis=1, inplace=True)
        return df

    def get_scaler(self):
        standard_scaler = preprocessing.StandardScaler()
        df = self.train_df.copy()
        # asi musim loopvat pres kazdy
        x = df.values  # returns a numpy array
        standard_scaler.fit(x)
        return standard_scaler

    def training(self):
        print("Training started")
        df = self.train_df

        # df["wards"] =  df[['wards_per_minute', 'wards_cleared_per_minute', 'pct_wards_cleared']].mean(axis=1)
        # df["c_wards"] = df[['c_wards_per_minute', 'c_wards_cleared_per_minute',
        #                   'c_pct_wards_cleared']].mean(axis=1)
       # df.drop(['wards_per_minute', 'wards_cleared_per_minute', 'pct_wards_cleared', 'c_wards_per_minute', 'c_wards_cleared_per_minute',
        #                  'c_pct_wards_cleared'], axis=1, inplace=True)
        #df.drop(["cs_per_minute", "first_blood", "wards_per_minute", "pct_wards_cleared", "c_cs_per_minute" ,"c_first_blood", "c_wards_per_minute", "c_pct_wards_cleared",
         #        "wards_cleared_per_minute", "c_wards_cleared_per_minute", "herald_game_value", "c_herald_game_value"], axis=1, inplace=True)
        y = df.pop("main_team_won")
        # asi musim loopvat pres kazdy
        x = df.values  # returns a numpy array
        standard_scaler = preprocessing.StandardScaler()
        #for col in df.columns:
       #     df[col] =standard_scaler.fit_transform(df[col].values.reshape(-1, 1))

        #x_scaled = standard_scaler.fit_transform(x)
        #x_scaled = self.scaler.transform(x)
        #df_scaler = pd.DataFrame(x_scaled)
        #df = x_scaled
        X_train, X_test, y_train, y_test = train_test_split(df, y,
                                                            test_size=0.2)

        from sklearn.model_selection import cross_val_score
        from sklearn.linear_model import LogisticRegression
        from sklearn.naive_bayes import GaussianNB
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.ensemble import VotingClassifier


        clf1 = LogisticRegression(random_state=1)
        clf2 = RandomForestClassifier(n_estimators=50, random_state=1)
        clf3 = GaussianNB()
        eclf = VotingClassifier(
            estimators=[('lr', clf1), ('rf', clf2), ('gnb', clf3)],
            voting='soft')

        for clf, label in zip([clf1, clf2, clf3, eclf],
                                   ['Logistic Regression', 'Random Forest',
                                    'naive Bayes', 'Ensemble']):
            scores = cross_val_score(clf, df, y, cv=5, scoring='accuracy')

            print("Accuracy: %0.2f (+/- %0.2f) [%s]" % (
            scores.mean(), scores.std(), label))
        self.training_columns = df.columns
        print(f"Set training columns {self.training_columns}")
        model = LogisticRegression()

        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)
        print(f"model {model} scored {score}. Model set")
        self.model = model
        #self.save_model(model)


    def load_saved_model(self):

        return joblib.load('C:\\Users\\pavel\\Desktop\\filename.joblib')

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
        #clf = self.model
        labels = clf.classes_
        assert self.training_columns is not None, "Need to train first - testing"
        training_cols =  list(self.training_columns)
        try:
            training_cols.remove("main_team_won")
        except:
            pass
        row = row[training_cols]

        probabilities = clf.predict_proba(row)
        return self.format_one_prediction(labels, probabilities)

def try_mxnet(db_loc):
    from mxnet import nd, autograd, gluon
    import mxnet as mx
    from mxnet.gluon import nn

    pred = My_predictor(db_loc)
    df = pred.format_train_df(pred.load_train_df(db_loc))
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

    net = mx.gluon.nn.Sequential()
    with net.name_scope():
        net.add(gluon.nn.Embedding(30, 10))
        net.add(gluon.rnn.LSTM(20))
        net.add(gluon.nn.Dense(category_count, flatten=False))
   #  net.initialize()
   #
   #
   #
   #  with net.name_scope():
   #     net.add(gluon.nn.Dense(128, activation="relu"))
   #     net.add(gluon.nn.Dense(64, activation="relu"))
   #     net.add( nn.Dense(category_count))
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

# used for training new lol_db_models
if __name__ == "__main__":
    #try_mxnet()
    from config import DATABASE_URI

    db_url = f"{DATABASE_URI}lol"

    #try_mxnet(db_url)
    #exit()

    pred = My_predictor(db_url)

    df = pred.load_train_df(db_url)
    pred.training()

    df_with_names = pred.df_for_da
    sample = df_with_names.sample()

    team_name = sample["name"]
    competitor_name = sample["c_name"]
    sample.drop(["c_name", "name"], axis=1, inplace=True)
    predictions = pred.predict_one_match(sample)


    print()
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


