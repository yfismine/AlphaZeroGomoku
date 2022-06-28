#include"GomokuBoard.h"
#include"APV_MCTS.h"
#include"NeuralNet.h"	
#include<iostream>
#include<string>
using namespace std;
int getMax_index(vector<double>& vec)
{
	int index = 0;
	double pro = -1;
	for (int i = 0; i < 225; ++i)
	{
		if (vec[i] > pro)
		{
			pro = vec[i];
			index = i;
		}
	}
	return index;
}
int main(void)
{
	GomokuBoard board;
	//NeuralNet net("F:\\毕设\\python脚本\\venv\\Include\\Models\\Libtorch\\best_model.pt", true, 64);
	NeuralNet net("Models/Libtorch/current_model.pt", true, 64);
	MCTS mcts1(&net, 64, 2500, 225, 5, 3, 0);
	int cnt = 0;
	int index;
	while (board.getBoardState() == GomokuBoard::BoardState::NO_END)
	{
		vector<double> plicy_value;
		if (cnt % 2 == 0)
		{
			auto t1 = clock();
			plicy_value = mcts1.getActionProbs(&board, 0);
			auto t2 = clock();
			index = getMax_index(plicy_value);
			cout << "当前AI胜利概率:" << mcts1.getValue() << endl;
			cout << "AI思考耗时：" << t2 - t1 << endl;
		}
		else
		{
			string str;
			cin >> str;
			int row = isdigit(str[0]) ? str[0] - '1' : str[0] - 'a'+9;
			int col = str[1] - 'A';
			index = row * 15 + col;
		}
		board.executeMove(index);
		board.display();
		mcts1.update(index);
		++cnt;
	}
	if (board.getBoardState() == GomokuBoard::BoardState::BLACK_WIN)
		cout << "black" << endl;
	else
		cout << "white" << endl;
	cout << cnt << endl;
}
