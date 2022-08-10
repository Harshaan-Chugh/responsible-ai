import RAI
from RAI.dataset import Feature, Data, MetaDatabase, Dataset
from RAI.AISystem import AISystem, Model, Task
import sklearn.metrics
import numpy as np


# Get Dataset
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
x, y = load_breast_cancer(return_X_y=True)
xTrain, xTest, yTrain, yTest = train_test_split(x, y)

nums = np.ones((xTrain.shape[0], 1))
nums[:int(xTrain.shape[0]/2)] = 0
xTrain = np.hstack((xTrain, nums))

nums = np.ones((xTrain.shape[0], 1))
nums[:int(xTrain.shape[0]/2)] = 0
xTrain = np.hstack((xTrain, nums))


nums = np.ones((xTest.shape[0], 1))
nums[:int(xTest.shape[0]/2)] = 0
xTest = np.hstack((xTest, nums))

nums = np.ones((xTest.shape[0], 1))
nums[:int(xTest.shape[0]/2)] = 0
xTest = np.hstack((xTest, nums))

# Set up features
features_raw = load_breast_cancer().feature_names
features = []

for feature in features_raw:
    features.append(Feature(feature, "float32", feature))
features.append(Feature("race", "integer", "race value", categorical=True, values=[{0:"black"}, {1:"white"}]))
features.append(Feature("gender", "integer", "race value", categorical=True, values=[{1:"male"}, {0:"female"}]))

# Hook data in with our Representation
training_data = Data(xTrain, yTrain)  # Accepts Data and GT
test_data = Data(xTest, yTest)
dataset = Dataset(training_data, test_data=test_data)  # Accepts Training, Test and Validation Set
meta = MetaDatabase(features)

# Create a model to make predictions
from sklearn.ensemble import RandomForestClassifier
reg = RandomForestClassifier(n_estimators=10, criterion='entropy', random_state=0)
model = Model(agent=reg, name="cisco_cancer_ai", display_name="Cisco Health AI", model_class="Random Forest Classifier", adaptive=False)
# Indicate the task of the model
task = Task(model=model, type='binary_classification', description="Detect Cancer in patients using skin measurements")

# Create AISystem from previous objects. AISystems are what users will primarily interact with.
configuration = {"fairness": {"priv_group": {"race": {"privileged": 1, "unprivileged": 0}},
                              "protected_attributes": ["race"], "positive_label": 1}}
ai = AISystem(meta_database=meta, dataset=dataset, task=task, user_config=configuration)
ai.initialize()

# Train model
reg.fit(xTrain, yTrain)


'''
train_preds = reg.predict(xTrain)
# Make Predictions
ai.compute_metrics(train_preds, data_type="train")
# Function to compare our result to sklearn's result.


resv_f = ai.get_metric_values_flat()
resv_d = ai.get_metric_values_dict()
resi_f = ai.get_metric_info_flat()
resi_d = ai.get_metric_info_dict()

print("TRAINING PREDICTION METRICS:")
for key in resv_f:
    if hasattr(resv_f[key], "__len__"): 
        # print(resi_f[key]['display_name'], " = ", 'list ...')
        print(resi_f[key]['display_name'], " = ", resv_f[key])
    else:
        print(resi_f[key]['display_name'], " = ", resv_f[key])
'''

print("\n\nTESTING PREDICTING METRICS:")
test_preds = reg.predict(xTest)
ai.compute_metrics(test_preds, data_type="test")








resv_f = ai.get_metric_values_flat()
resi_f = ai.get_metric_info_flat()
for key in resv_f:
    if hasattr(resv_f[key], "__len__"):
        # print(resi_f[key]['display_name'], " = ", 'list ...')
        print(resi_f[key]['display_name'], " = ", resv_f[key])
    else:
        print(resi_f[key]['display_name'], " = ", resv_f[key])


# Getting Metric Information
print("\nGetting Metric Information")
metric_info = ai.get_metric_info_flat()
for metric in metric_info:
    print(metric_info[metric])
 
# Get Model Information
print("\nGetting Model Info:")
res = ai.get_model_info()
print(res)

# Demonstrating Searching
query = "Bias"
print("\nSearching Metrics for ", query)
result = ai.search(query)
print(result)

# reset all previous keys
# ai.reset_redis()

# export to redis
ai.export_data_flat("Testing New Features")


# TEMPORARY WAY TO EXPORT CERTIFICATE VALUES
# Will be done in another file
print("Exporting Certificate Data")
ai.export_certificates()


print("\nViewing GUI")
# ai.viewGUI()
print("DONE")

print("\nSearching Metrics for ", query)
result = ai.search(query)
print(result)

