import pandas as pd
import numpy as np
from sklearn.externals import joblib
from config import ROOT_DIR
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class CommonPredictor:

    def __init__(self):
        self.scaler = None
        self.name = type(self).__name__
        self.model = self.load_saved_model()
        self.new_model = None
        self.X_train, self.X_test, self.y_train, self.y_test = \
            (None, None, None, None)
        self.training_columns = []
        self.y_col_name = ''

    def compare_models(self):

        self.check_differences(self.model)

        print(
            f"Old model stats {self.check_differences(self.model)} "
            f"and score {self.model.score(self.X_test, self.y_test):.2f}%"
        )
        print(
            f"New model stats {self.check_differences(self.new_model)} "
            f"and score {self.new_model.score(self.X_test, self.y_test):.2f}%"
        )

    def check_differences(self, clf):

        labels = clf.classes_

        probabilities = clf.predict_proba(self.X_test)
        real = self.y_test
        probs = pd.DataFrame(probabilities, columns=labels)
        t = pd.concat([probs, real.reset_index(drop=True)], axis=1)
        t["predicted"] = np.where(t[False] > 0.5, False, True)
        wrong = t[t["t1_winner"] != t["predicted"]]
        extremely_wrong = wrong[(wrong[False] > 0.8) | (wrong[False] < 0.2)]
        return f"got {len(extremely_wrong)} extremely wrong from {len(real)}" \
               f" which is {len(extremely_wrong)/len(real):.3f}%"

    def load_saved_model(self):
        return joblib.load(f'{ROOT_DIR}/data/{self.name}.joblib')

    def save_model(self, classifier):

        if input("U are going to rewrite model. Are you sure?"
                 " Spec 'yes' if so") == "yes":
            joblib.dump(classifier, f'{ROOT_DIR}/data/{self.name}.joblib')
            return True
        else:
            print("New model not set")
            return False

    def predict_one_match(self, row):
        clf = self.model
        labels = clf.classes_
        row = row[self.training_columns]

        probabilities = clf.predict_proba(row)
        return {labels[0]: probabilities[0][0],
                labels[1]: probabilities[0][1]}

    def train_on_whole(self):
        pass
