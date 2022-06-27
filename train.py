from policy_value_net import PolicyValueNet
from CppLibs import GomokuBoard, NeuralNet, MCTS
import numpy as np
import time
import threading
import concurrent.futures
from collections import deque
import random
import pickle
import os
from shutil import copy
from Scripts_function import *


class TrainPipeline:
    def __init__(self, config):
        self.config = config
        self.policy_value_net = PolicyValueNet(self.config["n"], self.config["use_gpu"],
                                               self.config["train_model_path"] + "current_model.pt")
        self.train_buffer = deque([], maxlen=self.config["max_buffer_len"])
        self.load_samples(self.config["samples_path"])
        self.end_train=False
    def run(self):
        for iter in range(1, self.config["train_iters"] + 1):
            print("Iter: {} Current Time: {}".format(iter, time.ctime(time.time())))
            net = NeuralNet(self.config["model_path"] + "current_model.pt", self.config["use_gpu"],self.config["thread_num"])
            # 充分利用利用CPU与GPU,使得训练数据的生成与训练部分并行
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["self_play_threadNum"]) as executor:
                # curThreadNum = self.config["self_play_threadNum"]
                sum_steps=0
                all_tasks = [executor.submit(self.self_play, net) for _ in range(0, self.config["self_play_threadNum"])]
                for id, future in enumerate(concurrent.futures.as_completed(all_tasks), start=1):
                    data, step, time_consume = future.result()
                    self.train_buffer.extend(data)
                    sum_steps+=step
                    # curThreadNum -= 1
                    # net.setBatchSize(curThreadNum * self.config["thread_num"])
                    print("itre{} id:{} time consumption:{}  step number:{}".format(iter, id, time_consume, step))
            avg_steps=sum_steps/self.config["self_play_threadNum"]
            if 0<=avg_steps<35:
                self.config["lr"]=0.01
            elif 35<=avg_steps<70:
                self.config["lr"]=0.001
            else:
                self.config["lr"]=0.0001
            print("avg_step:{} lr:{}".format(avg_steps, self.config["lr"]))
            del net
            if iter % self.config["trainSamples_save_freq"] == 0:
                self.save_samples(self.config["samples_path"])
            self.train(iter)
            if iter % self.config["comparison_freq"] == 0:
                current_net = NeuralNet(self.config["model_path"] + "current_model.pt", self.config["use_gpu"],
                                        self.config["thread_num"])
                best_net = NeuralNet(self.config["model_path"] + "best_model.pt", self.config["use_gpu"],
                                     self.config["thread_num"])
                results = self.contest(current_net, best_net)
                win_rate = results["Win"] / self.config["comparison_times"]
                print("*****************************contest end*******************************")
                print("our current model total Win:{} Draw:{} Loss:{}".format(results["Win"], results["Draw"],
                                                                              results["Loss"]))
                print("current update threshold:{:.2f} current model win rate:{:.2f}".format(
                    self.config["update_threshold"], win_rate))
                if win_rate >= self.config["update_threshold"]:
                    name = "best_model.pt"
                    self.policy_value_net.save_model(self.config["train_model_path"] + name,
                                                     self.config["model_path"] + name)
                    print("we get new best model")
                else:
                    print("we also use old best model")
                del current_net
                del best_net

    def run_byYixin(self):
        for iter in range(1, self.config["train_iters"] + 1):
            if iter % 2 != 0:
                game_name="Yixin vs Gomoku AI"
                net = NeuralNet(self.config["model_path"] + "current_model.pt", self.config["use_gpu"],
                                self.config["thread_num"])
            else:
                game_name="Yixin vs Yixin"
                net = None
            print("Iter: {} Type: {} Current Time: {}".format(iter,game_name, time.ctime(time.time())))
            # 充分利用利用CPU与GPU,使得训练数据的生成与训练部分并行
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                self.end_train=False
                task=executor.submit(self.self_play_byYixin,net)
                executor.submit(self.train,iter)
                data, step, time_consume, result = task.result()
                self.end_train=True
            print("itre{} time consumption:{}  step number:{} result: {}".format(iter, time_consume, step,result))
            self.train_buffer.extend(data)
            if iter % self.config["trainSamples_save_freq"] == 0:
                self.save_samples(self.config["samples_path"])
            if iter % self.config["comparison_freq"] == 0:
                current_net = NeuralNet(self.config["model_path"] + "current_model.pt", self.config["use_gpu"],
                                        self.config["thread_num"])
                best_net = NeuralNet(self.config["model_path"] + "best_model.pt", self.config["use_gpu"],
                                     self.config["thread_num"])
                results = self.contest(current_net, best_net)
                win_rate = results["Win"] / self.config["comparison_times"]
                print("*****************************contest end*******************************")
                print("our current model total Win:{} Draw:{} Loss:{}".format(results["Win"], results["Draw"],
                                                                              results["Loss"]))
                print("current update threshold:{:.2f} current model win rate:{:.2f}".format(
                    self.config["update_threshold"], win_rate))
                if win_rate >= self.config["update_threshold"]:
                    name = "best_model.pt"
                    self.policy_value_net.save_model(self.config["train_model_path"] + name,
                                                     self.config["model_path"] + name)
                    print("we get new best model")
                else:
                    print("we also use old best model")
    def train(self, iter):
        name = "current_model.pt"
        epochs=min(len(self.train_buffer)//self.config["batch_size"],self.config["epochs"])
        temp_train_buffer=random.sample(self.train_buffer,epochs*self.config["batch_size"])
        random.shuffle(temp_train_buffer)
        test_data=list(zip(*temp_train_buffer[:self.config["batch_size"]]))
        old_probs, old_v = self.policy_value_net.getActionProbs_Value(test_data[0])
        for epoch in range(1, epochs + 1):
            if self.end_train:
                break;
            train_examples = temp_train_buffer[(epoch-1)*self.config["batch_size"]:epoch*self.config["batch_size"]]
            train_data = list(zip(*train_examples))
            loss, policy_loss, value_loss = self.policy_value_net.train_step(train_data,self.config["lr"])
            print("iter:{} epoch:{},loss:{} policy_loss:{} value_loss:{}".format(
                    iter, epoch, loss, policy_loss, value_loss))
        new_probs, new_v = self.policy_value_net.getActionProbs_Value(test_data[0])
        kl = np.mean(np.sum(old_probs * (
                np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)),
                            axis=1)
                     )
        explained_var_old = (1 -
                             np.var(np.array(test_data[2]).flatten() - old_v.flatten()) /
                             np.var(np.array(test_data[2]).flatten()))
        explained_var_new = (1 -
                             np.var(np.array(test_data[2]).flatten() - new_v.flatten()) /
                             np.var(np.array(test_data[2]).flatten()))
        print("kl:{} evar_old:{} evar_new:{}".format(kl,explained_var_old,explained_var_new))  #避免GPU资源浪费其中的一个作为参考
        self.policy_value_net.save_model(self.config["train_model_path"] + name, self.config["model_path"] + name)

    def self_play_byYixin(self,net):
        board = GomokuBoard(self.config["n"], self.config["n_in_row"], self.config["moveCacheNum"])
        if net!=None:
            player = MCTS(net, self.config["thread_num"], self.config["mcts_branch_num"]+1500,
                          self.config["action_size"], self.config["c_puct"], self.config["c_virtual_loss"],
                          self.config["explore_prob"])
        train_data = {"board_data": [], "plicyProbs": [], "value": []}
        cnt = 0  # 计算回合数
        start = time.time()
        x=-1
        y=-1
        restart()
        while board.getBoardState() == board.NO_END:
            board_data = board.getBoardData()
            if net is None or cnt % 2==1:
                x, y = TURN(x, y)
                plicyProbs = self.config["action_size"] * [0]
                action = y * self.config["n"] + x
                plicyProbs[action] = 1
                equ_board_data, equ_plicyProbs = self.getEquiDataSet(board_data, plicyProbs)
                train_data["board_data"] += equ_board_data
                train_data["plicyProbs"] += equ_plicyProbs
                if net is not None:
                    player.update(action)
            else:
                plicyProbs = player.getActionProbs(board, 0)
                equ_board_data, equ_plicyProbs = self.getEquiDataSet(board_data, plicyProbs)
                train_data["board_data"] += equ_board_data
                train_data["plicyProbs"] += equ_plicyProbs
                action = np.argmax(plicyProbs)  # 确保尽可能强的落子被执行
                x, y = get_pos(action)
                player.update(action)
            board.executeMove(action)
            #board.display()
            cnt += 1
        end = time.time()
        state = board.getBoardState()
        if state == board.BLACK_WIN:
            flag = 1
        elif state == board.WHITE_WIN:
            flag = -1
        else:
            flag = 0
        for i in range(cnt):
            if i % 2 == 0:
                train_data["value"] += 8 * [[flag * 1]]
            else:
                train_data["value"] += 8 * [[flag * -1]]
        if state == board.DRAW:
            result = "Draw"
        elif state == board.BLACK_WIN:
            result = "Win"
        else:
            result = "Loss"
        return list(zip(train_data["board_data"], train_data["plicyProbs"], train_data["value"])), cnt, end - start,result

    def self_play(self, net):
        board = GomokuBoard(self.config["n"], self.config["n_in_row"], self.config["moveCacheNum"])
        player1 = MCTS(net, self.config["thread_num"], self.config["mcts_branch_num"],
                       self.config["action_size"], self.config["c_puct"], self.config["c_virtual_loss"],self.config["explore_prob"])
        player2 = MCTS(net, self.config["thread_num"], self.config["mcts_branch_num"],
                       self.config["action_size"], self.config["c_puct"], self.config["c_virtual_loss"],self.config["explore_prob"])
        train_data = {"board_data": [], "plicyProbs": [], "value": []}
        temp = self.config["temp"]  # 初始温度
        cnt = 0  # 计算回合数
        start = time.time()
        while board.getBoardState() == board.NO_END:
            board_data = board.getBoardData()
            if cnt % 2 == 0:
                plicyProbs = player1.getActionProbs(board, temp)
            else:
                plicyProbs = player2.getActionProbs(board, temp)
            equ_board_data, equ_plicyProbs = self.getEquiDataSet(board_data, plicyProbs)
            train_data["board_data"] += equ_board_data
            train_data["plicyProbs"] += equ_plicyProbs
            # list: plicyProbs to numpy: plicyProbs
            plicyProbs = np.array(plicyProbs)
            legal_moves = board.getAvailableMove()
            # 狄利克雷噪声 P(s,a)=(1-theta)*pi+theta*Dir(alpha)
            noise = self.config["dirichlet_theta"] * np.random.dirichlet(
                self.config["dirichlet_alpha"] * np.ones(np.count_nonzero(legal_moves)))
            plicyProbs = (1 - self.config["dirichlet_theta"]) * plicyProbs
            index = 0
            for i in range(len(plicyProbs)):
                if legal_moves[i] == 1:
                    plicyProbs[i] += noise[index]
                    index += 1
            plicyProbs /= np.sum(plicyProbs)
            # 按照plicyProbs的概率随机选择一个移动
            action = np.random.choice(len(plicyProbs), p=plicyProbs)
            board.executeMove(action)
            # print("board execute move {} ".format(action))
            #board.display()
            player1.update(action)
            player2.update(action)
            cnt += 1
            if cnt >= self.config["explore_threshold"]:  # 对弈超过探索阈值的部分将温度降为0，及使用尽可能好的移动
                temp = 0
        # 根据最终局面填补 value
        end = time.time()
        state = board.getBoardState()
        if state == board.BLACK_WIN:
            flag = 1
        elif state == board.WHITE_WIN:
            flag = -1
        else:
            flag = 0
        for i in range(cnt):
            if i % 2 == 0:
                train_data["value"] += 8 * [[flag * 1]]
            else:
                train_data["value"] += 8 * [[flag * -1]]
        return list(zip(train_data["board_data"], train_data["plicyProbs"], train_data["value"])), cnt, end - start

    def getEquiDataSet(self, board_data, plicyProbs):
        input = np.array(board_data)
        pi = np.array(plicyProbs).reshape(self.config["n"], self.config["n"])
        train_data = {"board_data": [], "plicyProbs": []}
        for i in range(0, 4):
            # 旋转
            n_input = np.rot90(input, i, axes=(1, 2))
            n_pi = np.rot90(pi, i)
            train_data["board_data"].append(n_input.tolist())
            train_data["plicyProbs"].append(n_pi.ravel().tolist())
            # 左右镜像
            n_input = np.flip(n_input, axis=2)
            n_pi = np.flip(n_pi, axis=1)
            train_data["board_data"].append(n_input.tolist())
            train_data["plicyProbs"].append(n_pi.ravel().tolist())
        return train_data["board_data"], train_data["plicyProbs"]

    def contest(self, current_net, best_net):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["comparison_times"]) as executor:
            all_tasks = [executor.submit(self.contest_helper, current_net, best_net, id) for id in
                         range(0, self.config["comparison_times"])]
            results = {"Win": 0, "Draw": 0, "Loss": 0}
            for index, future in enumerate(concurrent.futures.as_completed(all_tasks), start=1):
                result, step, time_consume = future.result()
                if result == 1:
                    results["Win"] += 1
                    print("cotest {} result: Win  ".format(index), end="")
                elif result == 0:
                    results["Draw"] += 1
                    print("contest {} result: Draw  ".format(index), end="")
                else:
                    results["Loss"] += 1
                    print("contest {} result: Loss  ".format(index), end="")
                print("step num:{} time consumption: {}".format(step, time_consume))
            return results

    def contest_helper(self, current_net, best_net, id):
        board = GomokuBoard(self.config["n"], self.config["n_in_row"], self.config["moveCacheNum"])
        player1 = MCTS(current_net, self.config["thread_num"], self.config["mcts_branch_num"],
                       self.config["action_size"], self.config["c_puct"], self.config["c_virtual_loss"],1)
        player2 = MCTS(best_net, self.config["thread_num"], self.config["mcts_branch_num"],
                       self.config["action_size"], self.config["c_puct"], self.config["c_virtual_loss"],1)
        cnt = 0  # 计算回合数
        start = time.time()
        while board.getBoardState() == board.NO_END:
            if (cnt + id) % 2 == 0:
                plicyProbs = player1.getActionProbs(board, 0)
            else:
                plicyProbs = player2.getActionProbs(board, 0)
            action = np.argmax(plicyProbs)  # 确保尽可能强的落子被执行
            board.executeMove(action)
            player1.update(action)
            player2.update(action)
            cnt += 1
        end = time.time()
        state = board.getBoardState()
        if state == board.DRAW:
            result = 0
        elif (state == board.BLACK_WIN and id % 2 == 0) or (state == board.WHITE_WIN and id % 2 == 1):
            result = 1
        else:
            result = -1
        return result, cnt, end - start

    def load_samples(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                self.train_buffer.extend(pickle.load(file))

    def save_samples(self, file_path):
        with open(file_path, "wb") as file:
            pickle.dump(self.train_buffer, file)


if __name__ == "__main__":
    from config import config
    #time.sleep(14400)
    pipeline = TrainPipeline(config)
    #net1 = NeuralNet(config["model_path"] + "current_model.pt", config["use_gpu"], config["thread_num"])
    #net2 = NeuralNet(config["model_path"] + "best_model.pt", config["use_gpu"], config["thread_num"])
    pipeline.run()
    #pipeline.run_byYixin()
    '''for i in range(10000):
        pipeline.train(i)'''
