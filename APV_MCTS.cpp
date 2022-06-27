#include "APV_MCTS.h"
#include<locale>
#include<cfloat>
#include<algorithm>
using namespace std;
/*所有结点的构造函数部分内部均不用加锁，这些函数只会在线程安全条件下被调用*/
TreeNode::TreeNode(const TreeNode& node)
{
	parent = node.parent;
	children = node.children;
	is_leaf = node.is_leaf;
	p_sa = node.p_sa;
	q_sa = node.q_sa;
	n_unobserved.store(node.n_unobserved.load());
	n_visited.store(node.n_visited.load());
	virtual_loss.store(node.virtual_loss.load());
}

TreeNode::TreeNode(TreeNode* parent, double p_sa):
	parent(parent),p_sa(p_sa){}

TreeNode& TreeNode::operator=(const TreeNode& node)
{
	if (this == &node)
		return *this;
	parent = node.parent;
	children = node.children;
	is_leaf = node.is_leaf;
	p_sa = node.p_sa;
	q_sa = node.q_sa;
	n_unobserved.store(node.n_unobserved.load());
	n_visited.store(node.n_visited.load());
	virtual_loss.store(node.virtual_loss.load());
	return *this;
}

unsigned int TreeNode::select(double c_puct, double c_virtual_loss)
{
	double best_value = -numeric_limits<double>::max();
	//因为只有当node非叶子时才会调用select故我们确保至少存在一个孩子
	unsigned int best_move = children.begin()->first;
	TreeNode* best_node = children.begin()->second;
	//保证select过程中children不会数据不会被更新
	{
		lock_guard<mutex> lock(children_lock);
		int sum_visited = n_visited + n_unobserved;  //提前保存sum_visited避免使用锁
		for (auto& [move, child] : children)
		{
			double cur_value = child->get_value(c_puct, c_virtual_loss, sum_visited);  //修正的sum_visited
			if (cur_value > best_value)
			{
				best_value = cur_value;
				best_move = move;
				best_node = child;
			}
		}
	}
	if (parent)
	{
		lock_guard<mutex> lock1(parent->children_lock); //其父节点是否请求执行了select
		++best_node->n_unobserved;
		++best_node->virtual_loss;
	}
	else
	{
		++best_node->n_unobserved;
		++best_node->virtual_loss;
	}
	return best_move;
}

void TreeNode::expand(const std::vector<double>& action_priors)
{
	std::lock_guard<std::mutex> lock(expand_lock);
	if (is_leaf)
	{
		unsigned int action_size = action_priors.size();
		for (unsigned int i = 0; i < action_size; i++)
		{
			if (abs(action_priors[i]) < FLT_EPSILON) continue;  //忽略掉概率太小的行动
			children[i] = new TreeNode(this, action_priors[i]);
		}
		is_leaf = false;
	}
}

void TreeNode::backup(double value)
{
	/*  Vir(s,a)=Vir(s,a)-1
	 *  O(s,a)=O(s,a)-1
	 *  Q(s,a)=Q(N(s,a)*Q(s,a)+V)/(N(s,a)+1)
	 */
	if (parent != nullptr)
		parent->backup(-value);  //parent的value是child的value的负数
	else
	{
		/*根结点不需要--virtual_loss和--n_unobserved*/

		{
			lock_guard<mutex> lock2(data_lock);   //确保其他线程的backup不会在计算q_sa时更新n_visited
			q_sa = (n_visited * q_sa + value) / (n_visited + 1);
		}

		n_visited++;
		return;
	}
	lock_guard<mutex> lock1(parent->children_lock);
	--virtual_loss;
	--n_unobserved;

	{
		lock_guard<mutex> lock2(data_lock);
		q_sa = (n_visited * q_sa + value) / (n_visited + 1);
	}

	n_visited++;
}

double TreeNode::get_value(double c_puct, double c_virtual_loss, unsigned int sum_n_visited)
{
	/*该函数本身一定是运行在线程安全的环境下的*/
	// WU-UCT
	double u = (c_puct * p_sa * sqrt(sum_n_visited) / (1 +n_visited+n_unobserved));
	// virtual loss
	double virLoss = c_virtual_loss * virtual_loss;
	// Value=Q(s,a)+WU-UCT-Virtual_Loss
	return n_visited == 0 ? u : ((q_sa * n_visited - virLoss) / n_visited + u);
}


MCTS::MCTS(NeuralNet* net, unsigned int thread_num, unsigned int mcts_branch_num , unsigned int action_size, double c_puct, double c_virtual_loss,double probs):
	net(net),thread_pool(thread_num),mcts_branch_num(mcts_branch_num),c_puct(c_puct),c_virtual_loss(c_virtual_loss),action_size(action_size),
	root(new TreeNode(nullptr,1.0),MCTS::tree_deleter),gen(time(0)),b_dist(probs){}  //probs是默认的探索概率

vector<double> MCTS::getActionProbs(GomokuBoard* gomoku, double temp)
{
	// submit simulate tasks to thread_pool
	std::vector<std::future<void>> futures;

	for (unsigned int i = 0; i < this->mcts_branch_num; i++)
	{
		// copy gomoku
		auto game = std::make_shared<GomokuBoard>(*gomoku);
		auto future =
			thread_pool.commit(std::bind(&MCTS::simulate, this, game));

		// future can't copy
		futures.emplace_back(std::move(future));
	}

	// wait simulate
	for (unsigned int i = 0; i < futures.size(); i++)
		futures[i].wait();

	// calculate probs
	std::vector<double> action_probs(action_size, 0);
	bool is_empty = true;
	auto* children_ptr = &root->children;  //使用指针避免复制
	if (root->q_sa > 0.9&&b_dist(gen))   //此时AI认为大概率会败，为了使得局面不落入常规局面,我们下一步以概率执行对方认为的最优点
	{
		unsigned int max_count = 0;
		unsigned int best_action = 0;
		for (auto& [action, child] : *children_ptr)
		{
			if (child->n_visited > max_count)
			{
				max_count = child->n_visited;
				best_action = action;
			}
		}
		children_ptr = &(*children_ptr)[best_action]->children;
	}
	// greedy
	if (abs(temp) < FLT_EPSILON)
	{
		unsigned int max_count = 0;
		unsigned int best_action = 0;
		for (auto& [action,child]:*children_ptr)
		{
			if (child->n_visited > max_count)
			{
				max_count = child->n_visited;
				best_action = action;
				is_empty = false;
			}
		}
		action_probs[best_action] = 1.;

	}
	else 
	{
		// explore
		double sum = 0;
		for (auto& [action, child] : *children_ptr)
		{
			if (child->n_visited > 0)
			{
				action_probs[action] = pow(child->n_visited, 1 / temp);
				sum += action_probs[action];
				is_empty = false;
			}
		}
		// pi(a|s)=N(s,a)^(1/t) / sum(N(s,a)^(1/t))
		if (sum != 0)
		{
			std::for_each(action_probs.begin(), action_probs.end(),
				[sum](double& x) { x /= sum; });
		}
	}
	if (is_empty)  //此时action_probs为全零值，我们将合法落子位置以等概率返回
	{
		auto legalMove = gomoku->getAvailableMove();
		int countOnes = count(legalMove.begin(), legalMove.end(), 1);
		vector<double> legalProbs(legalMove.begin(), legalMove.end());
		for_each(legalProbs.begin(), legalProbs.end(), [countOnes](double& x) {x=x / countOnes; });
		return legalProbs;
	}
	return action_probs;
}

void MCTS::update(unsigned int last_move)
{
	auto old_root = root.get();
	if (old_root->children[last_move] != nullptr) 
	{
		// 断链
		TreeNode* new_node = old_root->children[last_move];
		old_root->children[last_move] = nullptr;
		new_node->parent = nullptr;
		root.reset(new_node);
	}
	else
		root.reset(new TreeNode(nullptr, 1.));
}

void MCTS::simulate(std::shared_ptr<GomokuBoard> game)
{
	auto node = this->root.get();

	while (true) {
		if (node->get_is_leaf()) break;
		// select
		auto action = node->select(c_puct, c_virtual_loss);
		game->executeMove(action);
		node = node->children[action];
	}

	// get game status
	auto status = game->getBoardState();
	double value = 0;
	// NO_END
	if (status == GomokuBoard::BoardState::NO_END)
	{
		// predict action_probs and value by neural network
		std::vector<double> action_priors(action_size, 0);
		auto future = net->predict(game.get());
		auto result = future.get();
		action_priors = std::move(result.first);
		value = -result.second;   //当前局面的评分与当前结点的行动价值相反
		// mask invalid actions
		auto legal_moves = game->getAvailableMove();
		double sum = 0;
		for (int i = 0; i < action_size; ++i)
			legal_moves[i] == 1 ? (sum += action_priors[i]) : (action_priors[i] = 0);
		// renormalization
		if (sum > FLT_EPSILON)
		{
			std::for_each(action_priors.begin(), action_priors.end(),
				[sum](double& x) { x /= sum; });
		}
		else
		{
			//此次AI已经认为必败，随机将随机给出一个action
			sum = std::accumulate(legal_moves.begin(), legal_moves.end(), 0);
			for (unsigned int i = 0; i < action_priors.size(); i++) {
				action_priors[i] = legal_moves[i] / sum;
			}
		}
		// expand
		node->expand(action_priors);
	}
	else
	{
		//当其如果是终止状态是必定是当前node这一步就是必赢的，故其价值就是1
		if (status != GomokuBoard::BoardState::DRAW)
			value = 1;
	}
	node->backup(value);
}

void MCTS::tree_deleter(TreeNode* t)
{
	if (t == nullptr) return;
	for (auto [_, child] : t->children)
		tree_deleter(child);
	delete t;
}
