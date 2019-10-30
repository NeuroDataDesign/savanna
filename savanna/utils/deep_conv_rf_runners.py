import copy
import time
from multiprocessing import cpu_count

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from utils.dataset import get_subset_data
from inference.conv_rf import ConvRF
from rerf.RerF import fastPredict, fastRerF

RERF_NUM_TREES = 1000
RERF_TREE_TYPE = "binnedBase"




def run_one_layer_deep_conv_rf(dataset_name, data, choosen_classes, sub_train_indices, type="shared"):
    (train_images, train_labels), (test_images, test_labels) = get_subset_data(
        dataset_name, data, choosen_classes, sub_train_indices)

    time_taken = dict()

    # ConvRF (layer 1)
    if type == "rerf_shared":
        conv1 = ConvRF(type="rerf_shared", kernel_size=10, stride=2,
            num_trees = RERF_NUM_TREES, tree_type = RERF_TREE_TYPE)
    else:
        conv1 = ConvRF(type=type, kernel_size=10, stride=2)

    conv1_map = conv1.fit(train_images, train_labels)
    conv1_map_test = conv1.predict(test_images)
    time_taken = copy.deepcopy(conv1.time_taken)

    # Full RF
    train_start = time.time()
    if type == "rerf_shared":
        conv1_full_RF = fastRerF(X=conv1_map.reshape(len(train_images), -1),
                                 Y=train_labels,
                                 forestType=RERF_TREE_TYPE,
                                 trees=100,
                                 numCores=cpu_count() - 1)
    else:
        conv1_full_RF = RandomForestClassifier(n_estimators=100, n_jobs=-1)
        conv1_full_RF.fit(conv1_map.reshape(len(train_images), -1), train_labels)
    train_end = time.time()
    time_taken["train"] += (train_end - train_start)
    time_taken["final_fit"] = (train_end - train_start)

    test_start = time.time()
    if type == "rerf_shared":
        test_preds = fastPredict(conv1_map_test.reshape(len(test_images), -1), conv1_full_RF)
    else:
        test_preds = conv1_full_RF.predict(conv1_map_test.reshape(len(test_images), -1))
    test_end = time.time()
    time_taken["test"] += (test_end - test_start)
    time_taken["final_predict"] = (test_end - test_start)

    return accuracy_score(test_labels, test_preds), time_taken


def run_two_layer_deep_conv_rf(dataset_name, data, choosen_classes, sub_train_indices, type="shared"):
    (train_images, train_labels), (test_images, test_labels) = get_subset_data(
        dataset_name, data, choosen_classes, sub_train_indices)

    time_taken = dict()

    # ConvRF (layer 1)
    if type == "rerf_shared":
        conv1 = ConvRF(type="rerf_shared", kernel_size=10, stride=2,
            num_trees = RERF_NUM_TREES, tree_type = RERF_TREE_TYPE)
    else:
        conv1 = ConvRF(type=type, kernel_size=10, stride=2)
    conv1_map = conv1.fit(train_images, train_labels)
    conv1_map_test = conv1.predict(test_images)
    time_taken = copy.deepcopy(conv1.time_taken)

    # ConvRF (layer 2)
    if type == "rerf_shared":
        conv2 = ConvRF(type="rerf_shared", kernel_size=7, stride=1,
            num_trees = RERF_NUM_TREES, tree_type = RERF_TREE_TYPE)
    else:
        conv2 = ConvRF(type=type, kernel_size=7, stride=1)
    conv2_map = conv2.fit(conv1_map, train_labels)
    conv2_map_test = conv2.predict(conv1_map_test)
    for key in time_taken:
        time_taken[key] += conv2.time_taken[key]

    # Full RF
    train_start = time.time()
    if type == "rerf_shared":
        conv1_full_RF = fastRerF(X=conv2_map.reshape(len(train_images), -1),
                                 Y=train_labels,
                                 forestType=RERF_TREE_TYPE,
                                 trees=100,
                                 numCores=cpu_count() - 1)
    else:
        conv1_full_RF = RandomForestClassifier(n_estimators=100, n_jobs=-1)
        conv1_full_RF.fit(conv2_map.reshape(len(train_images), -1), train_labels)
    train_end = time.time()
    time_taken["train"] += (train_end - train_start)
    time_taken["final_fit"] = (train_end - train_start)

    test_start = time.time()
    if type == "rerf_shared":
        test_preds = fastPredict(conv2_map_test.reshape(len(test_images), -1), conv1_full_RF)
    else:
        test_preds = conv1_full_RF.predict(conv2_map_test.reshape(len(test_images), -1))
    test_end = time.time()
    time_taken["test"] += (test_end - test_start)
    time_taken["final_predict"] = (test_end - test_start)

    return accuracy_score(test_labels, test_preds), time_taken