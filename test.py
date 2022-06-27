<<<<<<< HEAD
import numpy as np
import time
import torch
from CppLibs import GomokuBoard
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from collections import deque
import random
import pickle
import copy
from config import config
train_buffer = deque([], maxlen=160000)
with open("./Data/checkpoint.example", "rb") as file:
    train_buffer.extend(pickle.load(file))
with open(r"F:\毕设\Gomoku\Data\checkpoint.example", "rb") as file:
    train_buffer.extend(pickle.load(file))
with open(r"./checkpoint.example", "wb") as file:
    pickle.dump(train_buffer, file)
=======
version https://git-lfs.github.com/spec/v1
oid sha256:f32d0bc1a77021c21e0c0ffa8997ed3a35b57318f86bc70930ba6e92534700ae
size 594
>>>>>>> 2673dac (pre)
