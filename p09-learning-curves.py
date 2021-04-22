import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier  # LongShortTerm memory
from shared import dataset_local_path, simple_boxplot
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample
import json
from sklearn.tree import DecisionTreeClassifier

from dataclasses import dataclass
from sklearn.base import ClassifierMixin

from typing import Dict, Any, List

#%% load up the data
examples = []
ys = []

# Load our data to list of examples:
with open(dataset_local_path("poetry_id.jsonl")) as fp:
    for line in fp:
        info = json.loads(line)
        keep = info["features"]
        ys.append(info["poetry"])
        examples.append(keep)

## CONVERT TO MATRIX:
feature_numbering = DictVectorizer(sort=True, sparse=False)
X = feature_numbering.fit_transform(examples)
del examples

## SPLIT DATA:
RANDOM_SEED = 12345678

# Numpy-arrays are more useful than python's lists.
y = np.array(ys)
# split off train/validate (tv) pieces.
rX_tv, rX_test, y_tv, y_test = train_test_split(
    X, y, train_size=0.75, shuffle=True, random_state=RANDOM_SEED
)
# split off train, validate from (tv) pieces.
rX_train, rX_vali, y_train, y_vali = train_test_split(
    rX_tv, y_tv, train_size=0.66, shuffle=True, random_state=RANDOM_SEED
)


scale = StandardScaler()
X_train = scale.fit_transform(rX_train)
X_vali: np.ndarray = scale.transform(rX_vali)  # type:ignore
X_test: np.ndarray = scale.transform(rX_test)  # type:ignore


@dataclass
class ExperimentResult:
    vali_acc: float
    params: Dict[str, Any]
    model: ClassifierMixin


#%% Actually compute performance for each % of training data
N = len(y_train)
num_trials = 100
percentages = list(range(5, 100, 5))
percentages.append(100)
scores = {}
acc_mean = []
acc_std = []

data_bucket = list(range(50, N, 50))
# Which subset of data will potentially really matter.
for n_samples in data_bucket:
    # n_samples = int((train_percent / 100) * N)
    print("{} samples...".format(n_samples))
    label = "{}".format(n_samples)

    # So we consider num_trials=100 subsamples, and train a model on each.
    scores[label] = []
    for i in range(num_trials):
        X_sample, y_sample = resample(
            X_train, y_train, n_samples=n_samples, replace=False
        )  # type:ignore
        # Note here, I'm using a simple classifier for speed, rather than the best.
        # clf = MLPClassifier(random_state=train_percent + i, max_iter=50000)
        clf = RandomForestClassifier(max_depth=4, random_state=RANDOM_SEED + i)
        clf.fit(X_sample, y_sample)
        # so we get 100 scores per percentage-point.
        scores[label].append(clf.score(X_vali, y_vali))
    # We'll first look at a line-plot of the mean:
    acc_mean.append(np.mean(scores[label]))
    acc_std.append(np.std(scores[label]))

# First, try a line plot, with shaded variance regions:
import matplotlib.pyplot as plt

# convert our list of means/std to numpy arrays so we can add & subtract them.
means = np.array(acc_mean)
std = np.array(acc_std)
# plot line from means
plt.plot(data_bucket, acc_mean, "o-")
# this is cool
# plot area from means & stddev
plt.fill_between(data_bucket, means - std, means + std, alpha=0.2)

# Manage axes/show:
plt.xlabel("Percent Training Data")
plt.ylabel("Mean Accuracy")
plt.xlim([0, N])
plt.title("Shaded Accuracy Plot")
plt.savefig("graphs/p09-area-Accuracy.png")
plt.show()


# Second look at the boxplots in-order: (I like this better, IMO)
simple_boxplot(
    scores,
    "Learning Curve",
    xlabel="Percent Training Data",
    ylabel="Accuracy",
    save="graphs/p09-boxplots-Accuracy.png",
)

# TODO: (practical tasks)
# 1. Swap in a better, but potentially more expensive classifier.
#    - Even DecisionTreeClassifier has some more interesting behavior on these plots.
# 2. Change the plots to operate over multiples of 50 samples, instead of percentages.
#    - This will likely be how you want to make these plots for your project.

# OPTIONAL CHALLENGE:
#  Refactor the code so that you can evaluate multiple models in this fashion.
#  Two different models at the same time will likely max out the visual utility of the plot.
#  The boxplot will not be able to show both models at once.