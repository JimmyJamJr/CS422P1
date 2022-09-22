import numpy as np
from numpy.random import default_rng
import data_storage


class Node:
    def __init__(self, data: int, decision: bool = False):
        self.left = None
        self.right = None
        self.data = data
        self.decision = decision


def preorder(node: Node):
    if node:
        if node.decision:
            print('_' + str(node.data), end=' ')
        else:
            print(node.data, end=' ')
        preorder(node.left)
        preorder(node.right)


# Input an array of labels, calculate the entropy
def entropy(labels: np.ndarray) -> float:
    classes = np.unique(labels)
    probabilities = np.fromiter((np.count_nonzero(labels == c) / len(labels) for c in classes), float)
    return np.sum(-probabilities * np.log2(probabilities))


# Function to recursively build the next layer of the tree using information gain
def build_next_layer(X: np.ndarray, Y: np.ndarray, remaining_features: list, depth: int, max_depth: int, H: float, tree: Node):
    # print("\n\nX:\n {} \nY: {} features: {} depth: {}".format(X, Y, remaining_features, depth))

    # If all labels are the same (entropy=0) return decision
    if H == 0:
        tree.data = Y[0]
        tree.decision = True
        # print("Decision: ", tree.data)
        return
    # If max_depth exceeded or no features remain, return decision based on current label percentage
    if depth > max_depth or len(remaining_features) == 0:
        yes_count = np.count_nonzero(Y == 1)
        no_count = np.count_nonzero(Y == 0)
        tree.data = 1 if yes_count > no_count else 0
        tree.decision = True
        # print("Decision: ", tree.data)
        return

    n_samples, _ = X.shape

    best_feature: int = -1
    best_IG: float = 0
    best_H_no: float = 0
    best_H_yes: float = 0
    best_no_indices: np.ndarray
    best_yes_indices: np.ndarray

    # Iterate through features
    for feature in remaining_features:
        no_indices = X[:, feature] == 0
        yes_indices = X[:, feature] == 1

        H_no = entropy(Y[no_indices])
        H_yes = entropy(Y[yes_indices])

        IG = H - (np.count_nonzero(no_indices) / n_samples * H_no) - (np.count_nonzero(yes_indices) / n_samples * H_yes)
        if IG > best_IG:
            best_feature = feature
            best_IG = IG
            best_H_no = H_no
            best_H_yes = H_yes
            best_no_indices = no_indices
            best_yes_indices = yes_indices

    # If no more information to be gained, make decision based on current label percentage
    if best_IG == 0:
        yes_count = np.count_nonzero(Y == 1)
        no_count = np.count_nonzero(Y == 0)
        tree.data = 1 if yes_count > no_count else 0
        tree.decision = True
        # print("Decision: ", tree.data)
        return

    tree.data = best_feature
    # print("Best feature: ", best_feature)
    tree.left = Node(-1)
    tree.right = Node(-1)
    remaining_features.remove(best_feature)
    build_next_layer(X[best_no_indices], Y[best_no_indices], remaining_features, depth + 1, max_depth, best_H_no, tree.left)
    build_next_layer(X[best_yes_indices], Y[best_yes_indices], remaining_features, depth + 1, max_depth, best_H_yes, tree.right)


def DT_train_binary(X: np.ndarray, Y: np.ndarray, max_depth: int) -> Node:
    n_samples, n_features = X.shape
    assert n_samples == len(Y)

    root = Node(-1)
    build_next_layer(X, Y, list(range(n_features)), 1, max_depth, entropy(Y), root)
    return root


def DT_make_prediction(x: np.ndarray, DT: Node) -> int:
    while not DT.decision:
        if x[DT.data] == 0:
            DT = DT.left
        else:
            DT = DT.right
    return DT.data


def DT_test_binary(X: np.ndarray, Y: np.ndarray, DT: Node) -> float:
    n_samples, n_features = X.shape
    assert n_samples == len(Y)

    correct_count = 0
    for i in range(n_samples):
        if DT_make_prediction(X[i, :], DT) == Y[i]:
            correct_count += 1

    return correct_count / n_samples


def RF_build_random_forest(X: np.ndarray, Y: np.ndarray, max_depth: int, num_of_trees: int) -> list:
    n_samples, n_features = X.shape
    assert n_samples == len(Y)

    data = np.column_stack([X, Y])
    forest = []
    # Repeat for the number of trees
    for i in range(num_of_trees):
        # Create a data split consisting of a random 10% of the dataset
        data_split = default_rng().choice(data, size = int(.1 * len(X) + .5))
        X_split = data_split[1:, :-1].astype(float)
        Y_split = data_split[1:, -1].astype(int)
        tree = DT_train_binary(X_split, Y_split, max_depth)
        forest.append(tree)
    return forest


def RF_test_random_forest(X: np.ndarray, Y: np.ndarray, RF: list) -> float:
    n_samples, n_features = X.shape
    assert n_samples == len(Y)

    for i in range(len(RF)):
        print("DT {}: {}".format(i, DT_test_binary(X, Y, RF[i])))

    correct_count = 0
    for i in range(n_samples):
        sample_predictions = [0, 0]
        for tree in RF:
            prediction = DT_make_prediction(X[i, :], tree)
            sample_predictions[prediction] += 1
        most_predicted = 0 if sample_predictions[0] > sample_predictions[1] else 1
        if most_predicted == Y[i]:
            correct_count += 1

    return correct_count / n_samples


if __name__ == "__main__":
    with open("haberman.csv") as file:
        data = [[x.strip() for x in line.split(',')] for line in file]
        features, labels = data_storage.build_nparray(np.array(data))

        tree = DT_train_binary(features, labels, 3)
        print("Tree Accuracy: ", DT_test_binary(features, labels, tree))

        forest = RF_build_random_forest(features, labels, 3, 11)
        print("Forest accuracy: ", RF_test_random_forest(features, labels, forest))