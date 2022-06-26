<<<<<<< HEAD
import time

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import hiddenlayer as h


class Residual_Block(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(Residual_Block, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        # BatchNorm2d(）对小批量3d数据组成的4d输入进行批标准化操作
        # 主要为了防止神经网络退化
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.downsample = in_channels != out_channels or stride != 1
        self.downsample_conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride)
        self.downsample_bn = nn.BatchNorm2d(out_channels)
        self.inittialize()  # 参数初始化

    def inittialize(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight.data, nonlinearity='relu')

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        # 将单元的输入直接与单元输出加在一起
        if self.downsample:
            residual = self.downsample_conv(residual)
            residual = self.downsample_bn(residual)
        out += residual
        out = self.relu(out)
        return out


class Net(nn.Module):
    """策略价值神经网络模型"""

    def __init__(self, board_size):
        super(Net, self).__init__()
        self.board_size = board_size
        # common layers
        self.conv = nn.Conv2d(13, 256, kernel_size=3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(256)
        self.relu = nn.ReLU(inplace=True)
        self.residual = self.make_layer(Residual_Block, in_channels=256, out_channels=256, nb_block=7)
        self.flatten = nn.Flatten(1)
        # action policy layers
        self.act_conv1 = nn.Conv2d(256, 2, kernel_size=3, padding=1)
        self.act_bn = nn.BatchNorm2d(2)
        self.act_linear1 = nn.Linear(2 * board_size * board_size, board_size * board_size)
        self.logSoftmax = nn.LogSoftmax(dim=1)
        # state value layers
        self.val_conv1 = nn.Conv2d(256, 1, kernel_size=1, bias=False)
        self.val_bn = nn.BatchNorm2d(1)
        self.val_linear1 = nn.Linear(board_size * board_size, 256)
        self.val_linear2 = nn.Linear(256, 1)
        self.tanh = nn.Tanh()
        self.inittialize()  # 参数初始化

    def inittialize(self):
        nn.init.kaiming_uniform_(self.act_linear1.weight.data,nonlinearity="linear")
        nn.init.kaiming_normal_(self.val_linear1.weight.data,nonlinearity="relu")
        nn.init.xavier_normal_(self.val_linear2.weight.data,gain=nn.init.calculate_gain("tanh"))
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight.data, nonlinearity='relu')

    def make_layer(self, block, in_channels, out_channels, nb_block, stride=1):
        layers = [block(in_channels, out_channels, stride) for _ in range(nb_block)]
        return nn.Sequential(*layers)

    def forward(self, state_input):
        # common layers
        out = self.conv(state_input)
        out = self.bn(out)
        out = self.relu(out)
        out = self.residual(out)
        # action policy layers
        out_act = self.act_conv1(out)
        out_act = self.act_bn(out_act)
        out_act = self.relu(out_act)
        out_act = self.flatten(out_act)
        out_act = self.act_linear1(out_act)
        out_act = self.logSoftmax(out_act)
        # state value layers
        out_val = self.val_conv1(out)
        out_val = self.val_bn(out_val)
        out_val = self.relu(out_val)
        out_val = self.flatten(out_val)
        out_val = self.val_linear1(out_val)
        out_val = self.relu(out_val)
        out_val = self.val_linear2(out_val)
        out_val = self.tanh(out_val)
        return out_act, out_val


class PolicyValueNet:
    """策略加载神经网络"""

    def __init__(self, board_size, use_gpu=True, model_path=None):
        self.board_size = board_size
        self.l2_const = 1e-4  # coef of l2 penalty
        self.use_gpu = use_gpu
        # the policy value net module
        if self.use_gpu:
            self.policy_value_net = Net(self.board_size).cuda()
        else:
            self.policy_value_net = Net(self.board_size)
        self.optimizer = optim.Adam(self.policy_value_net.parameters(),
                                    weight_decay=self.l2_const)
        if model_path:
            params = torch.load(model_path)
            self.policy_value_net.load_state_dict(params["net_params"])
            self.optimizer.load_state_dict(params["optim_params"])
        x = torch.randn(1,13, 15, 15).cuda()
        graph = h.build_graph(self.policy_value_net,x)
        graph.save(path="model.png",format="png")

    def setLearsnRate(self, lr):
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr

    def getActionProbs_Value(self, board_state):
        if self.use_gpu:
            input_data = torch.FloatTensor(board_state).cuda()
        else:
            input_data = torch.FloatTensor(board_state)
        log_probs, value = self.policy_value_net(input_data)
        probs = np.array(torch.exp(log_probs).tolist())
        value = np.array(value.tolist())
        return probs, value

    def train_step(self, train_data, lr):
        """函数功能：小批量训练策略加载网络
           返回：总损失及其构成部分的损失值"""
        self.policy_value_net.train()
        if self.use_gpu:
            state_batch = torch.FloatTensor(train_data[0]).cuda()
            train_actProbs = torch.FloatTensor(train_data[1]).cuda()
            train_value = torch.FloatTensor(train_data[2]).cuda()
        else:
            state_batch = torch.FloatTensor(train_data[0])
            train_actProbs = torch.FloatTensor(train_data[1])
            train_value = torch.FloatTensor(train_data[2])
        # zero the parameter gradients
        self.optimizer.zero_grad()
        self.setLearsnRate(lr)
        # forward
        log_pre_actProbs, pre_value = self.policy_value_net(state_batch)
        # alphago zero define the loss = (z - v)^2 - pi^T * log(p) + c||theta||^2 there is same as it
        policy_loss = -torch.mean(torch.sum(train_actProbs * log_pre_actProbs, 1))
        value_loss = F.mse_loss(pre_value, train_value)
        loss = policy_loss + value_loss
        # backward and optimize
        loss.backward()
        self.optimizer.step()
        return loss.item(), policy_loss.item(), value_loss.item()

    def save_model(self, model_path1=None, model_path2=None):
        self.policy_value_net.eval()
        if model_path1:
            params = {"net_params": self.policy_value_net.state_dict(), "optim_params": self.optimizer.state_dict()}
            torch.save(params, model_path1)
        if model_path2:
            torch.jit.script(self.policy_value_net).save(model_path2)


if __name__ == '__main__':
    from torchsummary import summary
    model=PolicyValueNet(15,True).policy_value_net
    summary(model,input_size=(13,15,15),device="cuda")
    inputs=torch.zeros(600,13,15,15).cuda()
    from torch.profiler import profile, record_function, ProfilerActivity
    with profile(activities=[
        ProfilerActivity.CPU,ProfilerActivity.CUDA], profile_memory=True, record_shapes=True) as prof:
        with record_function("model_inference"):
            model(inputs)
    print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))
    #net = PolicyValueNet(15, True,model_path="./Models/Pytorch/current_model.pt")
    #net.save_model("./Models/Pytorch/current_model.pt", "./Models/Libtorch/current_model.pt")
    #net.save_model("./Models/Pytorch/best_model.pt", "./Models/Libtorch/best_model.pt")
=======
version https://git-lfs.github.com/spec/v1
oid sha256:105c9475b7bf9fcf285d566b5161ed856ea599e63599837c63a072d3dc6dece5
size 8395
>>>>>>> 2673dac (pre)
