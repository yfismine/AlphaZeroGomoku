<<<<<<< HEAD
﻿#include "GomokuBoard.h"
#include<exception>
#include<string>
#include<iostream>
#include <pybind11/pybind11.h>
using namespace std;
namespace py = pybind11;
using namespace pybind11::literals;
GomokuBoard::GomokuBoard(unsigned int n, unsigned int n_in_row, unsigned int moveCacheNum)
	:n(n),n_in_row(n_in_row),moveCache(moveCacheNum,NullSite),board(n,vector<PieceType>(n,PieceType::EMPTY)){}

GomokuBoard::BoardState GomokuBoard::getBoardState()
{
	if (moveCache.back() == NullSite)   //空棋盘未终止状态
		return BoardState::NO_END;
	vector<pair<int, int>> dirs{ {0,1},{1,1},{1,0},{1,-1},{0,-1} };
	int lastRow = moveCache.back() / n;
	int lastCol = moveCache.back() % n;
	for (auto dir : dirs)
	{
		int sum = 1;
		int curRow = lastRow + dir.first;
		int curCol = lastCol + dir.second;
		for (int i = 0; i < n_in_row-1; ++i)
		{
			if (curRow < 0 || curRow >= n || curCol < 0 || curCol >= n || (board[curRow][curCol] != board[lastRow][lastCol]))
				break;
			++sum;
			curRow = curRow + dir.first;
			curCol = curCol + dir.second;
		}
		if(sum>=n_in_row)
			return board[lastRow][lastCol] == PieceType::BLACK ? BoardState::BLACK_WIN : BoardState::WHITE_WIN;
		curRow = lastRow - dir.first;
		curCol = lastCol - dir.second;
		for (int i = 0; i < n_in_row - 1; ++i)
		{
			if (curRow < 0 || curRow >= n || curCol < 0 || curCol >= n || (board[curRow][curCol] != board[lastRow][lastCol]))
				break;
			++sum;
			curRow = curRow - dir.first;
			curCol = curCol - dir.second;
		}
		if (sum >= n_in_row)
			return board[lastRow][lastCol] == PieceType::BLACK ? BoardState::BLACK_WIN : BoardState::WHITE_WIN;
	}
	if (board_cnt == n * n)
		return BoardState::DRAW;
	else
		return BoardState::NO_END;
}

vector<unsigned int> GomokuBoard::getAvailableMove()
{
	vector<unsigned int> availableMove(n*n,0);
	for (int i = 0; i < n; ++i)
	{
		for (int j = 0; j < n; ++j)
		{
			if (board[i][j] == PieceType::EMPTY)
				availableMove[i * n + j] = 1;
		}
	}
	return availableMove;
}

void GomokuBoard::executeMove(unsigned int action)
{
	unsigned int row = action / n, col = action % n;
	if (row < n && col < n && board[row][col] == PieceType::EMPTY)
	{
		board[row][col] = curColor;
		moveCache.pop_front();
		moveCache.push_back(action);
		changeCurColor();
		++board_cnt;
	}
	else
		throw exception(std::logic_error("illegal row or col"));
}

torch::Tensor GomokuBoard::getBoardData()
{
	/*添加近几手黑白棋子局面x,y*/
	int index = moveCache.size();
	torch::Tensor x = torch::zeros({1, n,n }, torch::dtype(torch::kFloat32));
	torch::Tensor y = torch::zeros({1, n,n }, torch::dtype(torch::kFloat32));
	for (int i = 0; i < n; ++i)
	{
		for (int j = 0; j < n; ++j)
		{
			if (board[i][j] == curColor)
				x[0][i][j] = 1;
			else if (board[i][j] == anotherColor(curColor))
				y[0][i][j] = 1;
		}
	}
	torch::Tensor data = torch::cat({ x,y },0);
	while (index)
	{
		int move1 = moveCache[--index];
		if (move1 != NullSite)
			y[0][move1 / n][move1 % n] = 0;
		int move2 = moveCache[--index];
		if (move2 != NullSite)
			x[0][move2 / n][move2 % n] = 0;
		data = torch::cat({ data,x,y },0);
	}
	/*添加当前落子方的局面矩阵C*/
	if (curColor == PieceType::BLACK)
		data = torch::cat({ data,torch::ones({1,n,n},torch::dtype(torch::kFloat32)) }, 0);
	else
		data = torch::cat({ data,torch::zeros({1,n,n},torch::dtype(torch::kFloat32)) }, 0);
	int channels = moveCache.size() + 3;
	data = data.reshape({ 1,channels,n,n });
	return data;
}

GomokuBoard::BoardData GomokuBoard::getBoardData_py()
{
	/*添加近几手黑白棋子局面x,y*/
	int index = moveCache.size();
	vector<vector<int>> x(n, vector<int>(n, 0));
	vector<vector<int>> y(n, vector<int>(n, 0));
	for (int i = 0; i < n; ++i)
	{
		for (int j = 0; j < n; ++j)
		{
			if (board[i][j] == curColor)
				x[i][j] = 1;
			else if (board[i][j] == anotherColor(curColor))
				y[i][j] = 1;
		}
	}
	BoardData data{ x,y };
	while (index)
	{
		int move1 = moveCache[--index];
		if (move1 != NullSite)
			y[move1 / n][move1 % n] = 0;
		int move2 = moveCache[--index];
		if (move2 != NullSite)
			x[move2 / n][move2 % n] = 0;
		data.push_back(x);
		data.push_back(y);
	}
	/*添加当前落子方的局面矩阵C*/
	if (curColor == PieceType::BLACK)
		data.emplace_back(vector<vector<int>>(n, vector<int>(n, 1)));
	else
		data.emplace_back(vector<vector<int>>(n, vector<int>(n, 0)));
	return data;
}

void GomokuBoard::display()
{
	cout << endl << "  ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯ" << endl;
	vector<string> digits = { "１", "２", "３", "４", "５", "６", "７", "８", "９", "ａ", "ｂ", "ｃ", "ｄ", "ｅ", "ｆ" };
	for (int i = 0; i < n; ++i)
	{
		cout << digits[i];
		for (int j = 0; j < n; ++j)
		{
			if (i * n + j == moveCache.back())
			{
				cout << "◎";
				continue;
			}
			if (board[i][j] == PieceType::EMPTY)
			{
				if (i == 0)
				{
					if (j == 0)
						cout << "┏ ";
					else if (j == n - 1)
						cout << "┓ ";
					else
						cout << "┯ ";
				}
				else if (i == n - 1)
				{
					if (j == 0)
						cout << "┗ ";
					else if (j == n - 1)
						cout << "┛ ";
					else
						cout << "┷ ";
				}
				else if (j == 0)
					cout << "┠ ";
				else if (j == n - 1)
					cout << "┨ ";
				else
					cout << "┼ ";
			}
			else
				cout << (board[i][j] == PieceType::BLACK ? "○" : "●");
		}
		cout << endl;
	}
	cout << endl;
}

void GomokuBoard::display_py()
{
	py::print(u"\n  Ａ Ｂ Ｃ Ｄ Ｅ Ｆ Ｇ Ｈ Ｉ Ｊ Ｋ Ｌ Ｍ Ｎ Ｏ");
	vector<const char16_t*> digits = { u"１", u"２", u"３", u"４", u"５", u"６", u"７", u"８", u"９", u"ａ", u"ｂ", u"ｃ", u"ｄ", u"ｅ", u"ｆ" };
	for (int i = 0; i < n; ++i)
	{
		py::print(digits[i], "end"_a = "");
		for (int j = 0; j < n; ++j)
		{
			if (i * n + j == moveCache.back())
			{
				py::print(u"◎ ", "end"_a = "");
				continue;
			}
			if (board[i][j] == PieceType::EMPTY)
			{
				if (i == 0)
				{
					if (j == 0)
						py::print(u"┏ ", "end"_a = "");
					else if (j == n - 1)
						py::print(u"┓ ", "end"_a = "");
					else
						py::print(u"┯ ", "end"_a = "");
				}
				else if (i == n - 1)
				{
					if (j == 0)
						py::print(u"┗ ", "end"_a = "");
					else if (j == n - 1)
						py::print(u"┛ ", "end"_a = "");
					else
						py::print(u"┷ ", "end"_a = "");
				}
				else if (j == 0)
					py::print(u"┠ ", "end"_a = "");
				else if (j == n - 1)
					py::print(u"┨ ", "end"_a = "");
				else
					py::print(u"┼ ", "end"_a = "");
			}
			else
				py::print(board[i][j] == PieceType::BLACK ? u"○ " : u"● ", "end"_a = "");
		}
		py::print("");
	}
	py::print("");
}


void GomokuBoard::changeCurColor()
{
	curColor = anotherColor(curColor);
}

inline GomokuBoard::PieceType GomokuBoard::anotherColor(PieceType color)
{
	return color == PieceType::BLACK ? PieceType::WHITE : PieceType::BLACK;
}
=======
version https://git-lfs.github.com/spec/v1
oid sha256:f6986f98d67db36712a67e869af27a8207c3e33d557c0714f11b8db295ce2491
size 7077
>>>>>>> 2673dac (pre)
