#include <pybind11/pybind11.h>
#include<pybind11/stl.h>
#include"GomokuBoard.h"
#include"NeuralNet.h"
#include"APV_MCTS.h"
using namespace pybind11::literals;
namespace py = pybind11;
PYBIND11_MODULE(CppLibs, m)
{
	py::class_<GomokuBoard> board(m, "GomokuBoard");
	board.def(py::init<unsigned int, unsigned int, unsigned int>(),
		"n"_a = 15, "n_in_row"_a = 5, "moveCacheNum"_a = 10)
		.def("getBoardData", &GomokuBoard::getBoardData_py)
		.def("getBoardState", &GomokuBoard::getBoardState)
		.def("getAvailableMove", &GomokuBoard::getAvailableMove)
		.def("executeMove", &GomokuBoard::executeMove, "action"_a)
		.def("display", &GomokuBoard::display_py);
	py::enum_<GomokuBoard::BoardState>(board, "BoardState")
		.value("BLACK_WIN", GomokuBoard::BoardState::BLACK_WIN)
		.value("WHITE_WIN", GomokuBoard::BoardState::WHITE_WIN)
		.value("DRAW", GomokuBoard::BoardState::DRAW)
		.value("NO_END", GomokuBoard::BoardState::NO_END)
		.export_values();

	py::class_<NeuralNet>(m, "NeuralNet")
		.def(py::init<string, bool, unsigned int>(), "model_path"_a, "use_gpu"_a, "batch_size"_a)
		.def("setBatchSize", &NeuralNet::setBatchSize, "batch_size"_a);
	py::class_<MCTS>(m, "MCTS")
		.def(py::init<NeuralNet*, unsigned int, unsigned int, unsigned int, double, double, double>(), "net"_a, "thread_num"_a,
			"mcts_branch_num"_a, "action_size"_a, "c_puct"_a, "c_virtual_loss"_a, "probs"_a = 0.75)
		.def("getActionProbs", &MCTS::getActionProbs, "gomoku"_a, "temp"_a = 1)
		.def("update", &MCTS::update, "last_move"_a);
}