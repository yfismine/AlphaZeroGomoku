<<<<<<< HEAD
config = {
    # GomokuBoard
    "n": 15,
    "n_in_row": 5,
    "moveCacheNum": 10,
    # NeuralNet
    "model_path": "./Models/Libtorch/",
    "use_gpu": True,
    # MCTS
    "thread_num": 64,
    "mcts_branch_num": 1000,
    "c_puct": 5,
    "c_virtual_loss": 3,
    # train
    "train_model_path":"./Models/Pytorch/",
    "samples_path": "./Data/checkpoint.example",
    "train_iters": 1000,
    "batch_size": 512,
    "epochs": 15,
    "explore_threshold": 18,
    "dirichlet_alpha": 0.06,
    "dirichlet_theta": 0.25,
    "lr": 0.0005,
    "temp": 1,
    "self_play_threadNum":10,
    "max_buffer_len": 80000,   #训练数据的缓冲区支持数据条数
    "comparison_freq": 25,
    "comparison_times": 10,
    "update_threshold":0.55,
    "explore_prob":0.8,
    "trainSamples_save_freq":10,
    "Yixin_freq":5

}
config["action_size"] = config["n"] * config["n"]
=======
version https://git-lfs.github.com/spec/v1
oid sha256:6622eb0de86ee98222ea48e4b71909af57a2b641e68bab2403730fa6b1fa8ce4
size 910
>>>>>>> 2673dac (pre)
