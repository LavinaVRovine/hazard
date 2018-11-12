from keras.preprocessing.sequence import pad_sequences
from keras.models import Model
from keras.layers import Input, Embedding, LSTM, Lambda
import keras.backend as K
from keras.optimizers import Adadelta
from keras.callbacks import ModelCheckpoint
import keras.backend as K
from LOL_formatter import Formatter
from sqlalchemy import create_engine
import pandas as pd
from sklearn.model_selection import train_test_split


from config import DATABASE_URI

def load_train_df(db_location):
    engine = create_engine(db_location,
                           echo=False)
    return pd.read_sql("SELECT * FROM basic_predictions", engine)

def format_train_df( train_dataset):
    formatter = Formatter(train_dataset)
    df = formatter.main_reformat()
    df = formatter.drop_for_predict(df)
    # names NEEDED for DA
    #self.df_for_da = df.copy()
    df.drop(["name", "c_name"], axis=1, inplace=True)
    return df



db_url = f"{DATABASE_URI}lol"

df = load_train_df(db_url)
df = format_train_df(df)


y = df.pop("main_team_won")

X_train, X_validation, Y_train, Y_validation = train_test_split(df, y,
                                                            test_size=0.2)



team_cols = [col for col in df.columns if not col.startswith("c_")]
compet_cols = [col for col in df.columns if col.startswith("c_")]




# Split to dicts
X_train = {'left': X_train[team_cols], 'right': X_train[compet_cols]}
X_validation = {'left': X_validation[team_cols], 'right': X_validation[compet_cols]}
#X_test = {'left': test_df[team_cols], 'right': test_df[compet_cols]}

# Convert labels to their numpy representations
Y_train = Y_train.values
Y_validation = Y_validation.values
# Make sure everything is ok
assert X_train['left'].shape == X_train['right'].shape
assert len(X_train['left']) == len(Y_train)


# Model variables
n_hidden = 50
gradient_clipping_norm = 1.25
batch_size = 64
n_epoch = 25

def exponent_neg_manhattan_distance(left, right):
    ''' Helper function for the similarity estimate of the LSTMs outputs'''
    return K.exp(-K.sum(K.abs(left-right), axis=1, keepdims=True))

max_seq_length = 20

# The visible layer
left_input = Input(shape=(max_seq_length,), dtype='int32')
right_input = Input(shape=(max_seq_length,), dtype='int32')

#embedding_layer = Embedding(len(embeddings), embedding_dim, weights=[embeddings], input_length=max_seq_length, trainable=False)

# Embedded version of the inputs
#encoded_left = embedding_layer(left_input)
#encoded_right = embedding_layer(right_input)

# Since this is a siamese network, both sides share the same LSTM
shared_lstm = LSTM(n_hidden)

left_output = shared_lstm(encoded_left)
right_output = shared_lstm(encoded_right)

# Calculates the distance as defined by the MaLSTM model
malstm_distance = Lambda(function=lambda x: exponent_neg_manhattan_distance(x[0], x[1]),output_shape=lambda x: (x[0][0], 1))([left_output, right_output])

# Pack it all up into a model
malstm = Model([left_input, right_input], [malstm_distance])

# Adadelta optimizer, with gradient clipping by norm
optimizer = Adadelta(clipnorm=gradient_clipping_norm)

malstm.compile(loss='mean_squared_error', optimizer=optimizer, metrics=['accuracy'])

# Start training
training_start_time = time()

malstm_trained = malstm.fit([X_train['left'], X_train['right']], Y_train, batch_size=batch_size, nb_epoch=n_epoch,
                            validation_data=([X_validation['left'], X_validation['right']], Y_validation))

print("Training time finished.\n{} epochs in {}".format(n_epoch, datetime.timedelta(seconds=time()-training_start_time)))