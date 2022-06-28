#include<iostream>
#include<unordered_map>
#include<unordered_set>
#include<vector>
#include<time.h>
#include<deque>
#include<queue>
#include<time.h>
#include<atomic>
#include<locale>
#include<thread>
#include<atomic>
#include"GomokuBoard.h"
#include"ThreadPool.h"
#include"NeuralNet.h"
#include"APV_MCTS.h"
#include<random>
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
	NeuralNet net("Models/Libtorch/best_model.pt", true, 64);
	//NeuralNet net("C:\\Users\\Pilgrim\\Desktop\\Libtorch\\best_model.pt", true, 64);
	//NeuralNet net("F:\\GoogleDownload\\best_model1.pt", true, 64);
	//NeuralNet net("F:\\GoogleDownload\\current_model.pt", true, 64);
	MCTS mcts(&net, 64, 1500, 225, 5, 3,0);
	/*              Test 1                 */
	/*board.executeMove(49);
	board.executeMove(91);
	board.executeMove(50);
	board.executeMove(92);
	board.executeMove(51);
	board.executeMove(93);
	board.executeMove(52);
	board.executeMove(94);*/
	/*board.executeMove(51);
	board.executeMove(91);
	board.executeMove(49);
	board.executeMove(92);
	board.executeMove(50);
	board.executeMove(93);
	board.executeMove(1);*/
	/*board.executeMove(112);
	board.executeMove(113);
	board.executeMove(98);
	board.executeMove(84);
	board.executeMove(114);
	board.executeMove(130);
	board.executeMove(128);
	board.executeMove(142);
	board.executeMove(96);
	board.executeMove(144);
	board.executeMove(97);*/
	board.executeMove(112);
	board.executeMove(113);
	board.executeMove(128);
	board.executeMove(96);
	board.executeMove(142);
	board.executeMove(98);
	board.executeMove(114);
	board.executeMove(100);
	board.executeMove(99);
	board.executeMove(129);
	board.executeMove(145);
	board.executeMove(157);
	board.executeMove(131);
	board.executeMove(144);
	board.executeMove(159);
	board.executeMove(117);
	cout << board.getBoardData() << endl;
	board.display();
	auto probs = mcts.getActionProbs(&board);
	cout << "下一步最佳落子位置：" << getMax_index(probs) << endl;
	cout << "胜率：" << mcts.getValue() << endl;
}
