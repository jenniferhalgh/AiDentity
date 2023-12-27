from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
import sqlite3
import numpy as np
import keras
import pandas as pd
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from keras.utils import to_categorical
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import pickle
from keras.applications.vgg16 import preprocess_input
from PIL import Image
from keras.applications import vgg16
from keras.callbacks import EarlyStopping
from keras import regularizers
import time
import os
import json
from keras.models import save_model
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, confusion_matrix)
import numpy as np
from numpy import expand_dims
from keras.models import Model

class LoadDataset(BaseEstimator, TransformerMixin):
    def __init__(self, database_path):
        self.database_path = database_path
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        conn = sqlite3.connect(self.database_path)
        query = "SELECT * FROM faces"
        df = pd.read_sql_query(query, conn)
        df['image'] = df['image'].apply(lambda x: np.array(pickle.loads(x)))
        conn.close()
        return df, len(np.unique(df['target']))

class SplitDataset(BaseEstimator, TransformerMixin):
    def __init__(self, val_size=0.2, test_size=0.2, random_state=0):
        self.val_size = val_size
        self.test_size = test_size
        self.random_state = random_state
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        df, num_classes = X
        X_train, X_temp, y_train, y_temp = train_test_split(df['image'].values, df['target'].values, test_size=(self.val_size + self.test_size), random_state=self.random_state)

        # Split the temp set into validation and test sets
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=(self.test_size / (self.val_size + self.test_size)), random_state=self.random_state)

        # Print the shapes of the resulting sets
        print("Training set shape:", X_train.shape, y_train.shape)
        print("Validation set shape:", X_val.shape, y_val.shape)
        print("Testing set shape:", X_test.shape, y_test.shape)

        return X_train, X_val, X_test, y_train, y_val, y_test, num_classes


class Preprocess(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        X_train, X_val, X_test, y_train, y_val, y_test, num_classes = X

        # One-hot encode the labels
        y_train_categorical = keras.utils.to_categorical(y_train, num_classes)
        y_val_categorical = keras.utils.to_categorical(y_val, num_classes)
        y_test_categorical = keras.utils.to_categorical(y_test, num_classes)

        # Resize images to 224x224
        X_train = np.array([np.array(Image.fromarray(img).resize((47, 62))) for img in X_train])
        X_val = np.array([np.array(Image.fromarray(img).resize((47, 62))) for img in X_val])
        X_test = np.array([np.array(Image.fromarray(img).resize((47, 62))) for img in X_test])

        # Normalize the images
        X_train = preprocess_input(X_train)
        X_val = preprocess_input(X_val)
        X_test = preprocess_input(X_test)

        return X_train, X_val, X_test, y_train_categorical, y_val_categorical, y_test_categorical, num_classes

class TrainModel(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_train, X_val, X_test, y_train, y_val, y_test, num_classes = X
        model = Sequential()
        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(62,47,3)))
        model.add(MaxPooling2D(2, 2))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D(2, 2))
        model.add(Conv2D(128, (3, 3), activation='relu'))
        model.add(MaxPooling2D(2, 2))
        model.add(Conv2D(256, (3, 3), activation='relu'))
        model.add(MaxPooling2D(2, 2))
        model.add(Flatten())
        model.add(Dense(1024, activation='relu'))
        model.add(Dense(num_classes, activation='softmax'))
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=1, batch_size=10)
        print("Number of epochs:", len(history.history['loss']))
        return model, X_test, y_test

class VisualizeFeatureMaps(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        # Assuming X is a tuple (image, label)
        model, X_test, y_test = X
        
        image = X_test[0]

        conv_layer_indices = [i for i, layer in enumerate(model.layers) if isinstance(layer, Conv2D)]

        #Create a list to store convolutional layers
        conv_layers = [layer for layer in model.layers if isinstance(layer, Conv2D)]

        #Create a new model containing only the convolutional layers
        model2 = Model(inputs=model.inputs, outputs=[layer.output for layer in conv_layers])

        #Expand the dimensions of the input to match the model's expected input shape
        image = expand_dims(image, axis=0)

        #Get the feature maps
        feature_maps = model2.predict(image)
        summed_feature_maps = [fmap_list.sum(axis=-1) for fmap_list in feature_maps]

        #Plot the feature maps
        fig = plt.figure(figsize=(15, 15))
        layer_index = 0

        for summed_fmap in summed_feature_maps:
            ax = plt.subplot(len(conv_layers), 1, layer_index + 1)
            ax.set_xticks([])
            ax.set_yticks([])
            plt.imshow(summed_fmap[0, :, :], cmap='gray')

            layer_index += 1

        plt.show()
        return model, X_test, y_test
    
class EvaluateModel(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        model, X_test, y_test = X
        predicted_probabilities = model.predict(X_test)
        predicted_classes = np.argmax(predicted_probabilities, axis=1)

        if len(y_test.shape) > 1 and y_test.shape[1] > 1:
            y_test = np.argmax(y_test, axis=1)

        accuracy = accuracy_score(y_test, predicted_classes)
        precision = precision_score(y_test, predicted_classes, average='weighted')
        recall = recall_score(y_test, predicted_classes, average='weighted')
        f1 = f1_score(y_test, predicted_classes, average='weighted')
        print(accuracy, precision, recall, f1)
        return accuracy, precision, recall, f1, model


pipeline = Pipeline([
    ('load_dataset', LoadDataset(database_path='./lfw_augmented_dataset.db')),
    ('split_dataset', SplitDataset(test_size=0.2, random_state=0)),
    ('preprocess', Preprocess()),
    ('train_model', TrainModel()),
    ('visualize_feature_maps', VisualizeFeatureMaps()),
    ('evaluate_model', EvaluateModel())
])

#save model
def save_trained_model(model, accuracy, precision, recall, f1):
    # Save the trained model
    save_path = "../monorepo/Model/model_registry/"
    timestamp = time.strftime("%Y%m%d%H%M%S")
    model.save(f'{save_path}model_version_{timestamp}.h5')
    # when the model is initally trained the way we load the model gives 0.0 for all evaluation metrics
    # therefore, we save the evaluation metrics in a json file
    
    evaluation_metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    }

    metrics_file_path = os.path.join(save_path, 'evaluation_metrics.json')
    with open(metrics_file_path, 'w') as metrics_file:
        json.dump(evaluation_metrics, metrics_file)

# Run the pipeline
transformed_data = pipeline.transform(None)

accuracy, precision, recall, f1, model  = transformed_data

save_trained_model(model, accuracy, precision, recall, f1)

''''
#visualize feature maps
def visualize_feature_maps(model, image):
    #Get indices of convolutional layers
    conv_layer_indices = [i for i, layer in enumerate(model.layers) if isinstance(layer, Conv2D)]

    #Create a list to store convolutional layers
    conv_layers = [layer for layer in model.layers if isinstance(layer, Conv2D)]

    #Create a new model containing only the convolutional layers
    model2 = Model(inputs=model.inputs, outputs=[layer.output for layer in conv_layers])

    #Expand the dimensions of the input to match the model's expected input shape
    image = expand_dims(image, axis=0)

    #Get the feature maps
    feature_maps = model2.predict(image)
    summed_feature_maps = [fmap_list.sum(axis=-1) for fmap_list in feature_maps]

    #Plot the feature maps
    fig = plt.figure(figsize=(15, 15))
    layer_index = 0

    for summed_fmap in summed_feature_maps:
        ax = plt.subplot(len(conv_layers), 1, layer_index + 1)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(summed_fmap[0, :, :], cmap='gray')

        layer_index += 1

    plt.show()
#image = X_train[0]
#visualize_feature_maps(model, image)
'''