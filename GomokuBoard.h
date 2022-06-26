<<<<<<< HEAD
#pragma once
#include<vector>
#include<utility>
#include<deque>
#include<unordered_set>
#include<torch/script.h>
using std::pair;
using std::vector;
using std::deque;
using std::unordered_set;
class GomokuBoard
{
public:
	enum class PieceType:char {BLACK,WHITE,EMPTY};  //减少棋盘占用空间
	enum class BoardState {BLACK_WIN,WHITE_WIN,DRAW,NO_END};
	using Board = vector<vector<PieceType>>;
	using BoardData = vector<vector<vector<int>>>;
	GomokuBoard(unsigned int n=15, unsigned int n_in_row=5, unsigned int moveCacheNum=10);
	BoardState getBoardState();
	vector<unsigned int> getAvailableMove();
	void executeMove(unsigned int action);
	torch::Tensor getBoardData();   //获取棋盘的张量数据
	BoardData getBoardData_py();    //获取棋盘的张量数据 python版本
	void display();
	void display_py();             //python版本的display
private:
	const int NullSite = -1;
	unsigned int n;   //棋盘大小
	unsigned int n_in_row;  //胜利条件
	PieceType curColor=PieceType::BLACK;   //当前棋子颜色
	unsigned int board_cnt = 0;    //落子数
	deque<int> moveCache;  //近几手的落子位置
	vector<vector<PieceType>> board;
	inline void changeCurColor();
	inline PieceType anotherColor(PieceType color);
};

=======
version https://git-lfs.github.com/spec/v1
oid sha256:b397abf91020c3f57e926c5a2210f57003db632bf57c86f975cc74a5a704365f
size 1221
>>>>>>> 2673dac (pre)
