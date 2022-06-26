# AlphaZero_Gomoku
&emsp;&emsp;本项目主要是采用蒙特卡洛搜索树与残差神经网络实现的一个可在小规模硬 件设施上短期训练一个拥有较强棋力的五子棋 AI。参考 AlphaGo Zero 原始论文 《Mastering the game of Go without human knowledge》实现的一个在五子棋游 戏上的复现，实现过程中采用相应的原创性方法进行改进，使其算法更加适应项 目需求并最终取得的较好的效果。MCTS 部分使用 C++编写的带虚拟损失的树并 行版本的 Python 扩展，训练管道与神经网络部分均使用 Python 编写。


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![image1](https://github.com/yfismine/AlphaZero_Gomoku/raw/main/Image/win1.png)&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![image2](https://github.com/yfismine/AlphaZero_Gomoku/raw/main/Image/win2.png)  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; 模型与弈心的部分对弈棋谱（模型执黑）  

&emsp;&emsp;由于本人只在一块GTX1060的笔记本显卡上训练了3天，所以其实模型性能上还是可以有很大的提升的，但是这并不影响本项目的模型仍有棋力非常强劲，在无禁手规则下，理论上先手条件下人类玩家几乎无法战胜，后手条件下也以极大胜率战胜人类玩家，对战弈心的职业四段棋力,在先手条件下，也有小概率可以获胜（大约10局赢1到2局)
# 项目实现的功能
1. 人机对弈
2. 模型与弈心对弈
3. 模型自对弈强化学习

# 可能需要
Windows 10; NVIDIA显卡; Python 3.8; VS 2019; CUDA 11.3; PyTorch 1.10 Libtorch 1.10
# 文件结构
1. Data文件夹中保存的是模型自对弈训练过程中生成的部分数据
2. Models文件夹中保存的是模型数据，分别为Libtorch模型和Pytorch模型
# 安装弈心
运行YiXin2017_May.exe文件安装弈心程序

# 注意
1. 本程序并未编写图形界面部分的代码，为了使得人机对弈的体验更佳，我们使用的是弈心的对弈界面，所以在运行过程中尽量不要让窗口覆盖住弈心程序的窗口
2. 如果只想了解神经网络部分内容或者只是进行简单对弈体验棋力，不需要下载Libtorch,蒙特卡洛搜索树部分的代码我们已经打包为CppLibs.pyd(window) CppLibs.so(linux)，可以直接当成python扩展包进行调用
3. 各个文件的具体实现功能以及算法训练和原理在上述AlphaZero_Gomoku.pdf文档,其中进行了非常详细的讲解，可以进行浏览学习，有其他问题可以在issues中进行提问
# 模型与玩家对弈
1. 运行弈心程序
2. 直接运行Scripts_function.py文件
3. 在弈心的图像界面中进行落子对弈  
##### 提示：start函数中的cnt起始值决定玩家先手还是模型先手，0为模型先手，1为玩家先手可以自行设置，默认为模型先手

# 模型与弈心对弈
1. 运行弈心程序，可以自行设置弈心的难度
2. 将Scripts_function.py中start函数中的TURN_by_human替换为TURN
3. 运行Scripts_function.py文件，可以在弈心的程序窗口观看模型与弈心的对弈过程

# 训练
直接运行train.py文件即可，可在config.py文件中修改训练参数

# 致谢
本项目主要是在以下两位的工作基础上展开拓展的，非常感谢他们的工作  
1. https://github.com/junxiaosong/AlphaZero_Gomoku
2. https://github.com/hijkzzz/alpha-zero-gomoku
