import pandas as pd
from sklearn.model_selection import train_test_split
from RAI.AISystem import AISystem, Model
from RAI.dataset import Data, Dataset, Feature
from RAI.redis import RaiRedis
from RAI.utils import df_to_RAI
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier

use_dashboard = True

# Get Dataset
data_path = "../data/adult/"
train_data = pd.read_csv(data_path + "train.csv", header=0,
                         skipinitialspace=True, na_values="?")
test_data = pd.read_csv(data_path + "test.csv", header=0,
                        skipinitialspace=True, na_values="?")
all_data = pd.concat([train_data, test_data], ignore_index=True)

# convert aggregated data into RAI format
meta, X, y, output = df_to_RAI(all_data, target_column="income-per-year", normalize="Scalar", max_categorical_threshold=5)
xTrain, xTest, yTrain, yTest = train_test_split(X, y, random_state=1, stratify=y)

# Create a model to make predictions
reg = RandomForestClassifier(n_estimators=10, criterion='entropy', random_state=0)
model = Model(agent=reg, output_features=output, name="cisco_income_ai", predict_fun=reg.predict, predict_prob_fun=reg.predict_proba,
              description="Income Prediction AI", model_class="Random Forest Classifier", )
configuration = {"fairness": {"priv_group": {"race": {"privileged": 1, "unprivileged": 0}},
                              "protected_attributes": ["race"], "positive_label": 1},
                 "time_complexity": "polynomial"}

dataset = Dataset({"train": Data(xTrain, yTrain), "test": Data(xTest, yTest)})
ai = AISystem(name="AdultDB",  task='binary_classification', meta_database=meta, dataset=dataset, model=model)
ai.initialize(user_config=configuration)

reg.fit(xTrain, yTrain)

print("\n\nTESTING PREDICTING METRICS:")
test_preds = reg.predict(xTest)
ai.compute({"test": {"predict": test_preds}}, tag='model1')

if use_dashboard:
    r = RaiRedis(ai)
    r.connect()
    r.reset_redis()
    r.add_measurement()

reg2 = AdaBoostClassifier()
reg2.fit(xTrain, yTrain)
ai.model.agent = reg2
test_preds = reg2.predict(xTest)

ai.compute({"test": {"predict": test_preds}}, tag="model2")
v = ai.get_metric_values()
v = v["test"]
info = ai.get_metric_info()
if use_dashboard:
    r.add_measurement()

from RAI.Analysis import AnalysisManager

analysis = AnalysisManager()
print("available analysis: ", analysis.get_available_analysis(ai, "test"))
# result = analysis.run_analysis(ai, ["test"], ["FairnessAnalysis"])
result = analysis.run_all(ai, "test", "Test run!")
for analysis in result:
    print("Analysis: " + analysis)
    print(result[analysis].to_string())
