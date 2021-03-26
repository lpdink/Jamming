import numpy as np
import matplotlib.pyplot as plt


def run():
    x1 = np.load("./tests/saved/noise_data.npy")
    # y1 = np.load("./waves/train_y.npy")
    # x2 = np.load("./waves/test_x.npy")
    # y2 = np.load("./waves/test_y.npy")

    plt.subplot(2, 2, 1)
    plt.scatter(np.linspace(0, 1, num=len(x1)), x1, s=0.1)

    # plt.subplot(2, 2, 2)
    # plt.scatter(np.linspace(0, 1, num=len(y1)), y1, s=0.1)

    # plt.subplot(2, 2, 3)
    # plt.scatter(np.linspace(0, 1, num=len(x2)), x2, s=0.1)

    # plt.subplot(2, 2, 4)
    # plt.scatter(np.linspace(0, 1, num=len(y2)), y2, s=0.1)

    plt.show()
