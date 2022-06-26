<<<<<<< HEAD
#include "NeuralNet.h"
using namespace std;
NeuralNet::NeuralNet(string model_path, bool use_gpu, unsigned int batch_size):
	module(torch::jit::load(model_path.c_str())),
	use_gpu(use_gpu),batch_size(batch_size)
{
    module.eval();
	if (use_gpu) module.to(at::kCUDA);
	predictThread = thread([this] {
		while (running) {
			infer();
		}
	});
}

future<NeuralNet::ActProbs_Value> NeuralNet::predict(GomokuBoard* gomoku)
{
	auto data = gomoku->getBoardData();
	promise<ActProbs_Value> promise;
	auto ret = promise.get_future();

	{
		lock_guard<mutex> lock(this->lock);
		tasks.emplace(make_pair(data, std::move(promise)));
	}
	cv.notify_all();
	return ret;
}

NeuralNet::~NeuralNet()
{
	running = false;
	predictThread.join();
}

void NeuralNet::infer()
{
    // get inputs
    vector<Tensor> dataStack;
    vector<promise<ActProbs_Value>> promises;
    bool timeout = false;
    while (dataStack.size() < batch_size && !timeout) {
        // pop task
        {
            unique_lock<mutex> lock(this->lock);
            if (cv.wait_for(lock, 1ms,
                [this] { return tasks.size() > 0; })) {
                auto task = std::move(tasks.front());
                dataStack.emplace_back(std::move(task.first));
                promises.emplace_back(std::move(task.second));
                this->tasks.pop();
            }
            else
                timeout = true;
        }
    }

    // inputs empty
    if (dataStack.size() == 0)
        return;

    // infer
    std::vector<torch::jit::IValue> inputs{
        use_gpu ? torch::cat(dataStack,0).to(at::kCUDA)
                      : torch::cat(dataStack, 0) };
    auto result = module.forward(inputs).toTuple();
    torch::Tensor p_batch = result->elements()[0].toTensor().toType(torch::kFloat32).exp().to(at::kCPU);
    torch::Tensor v_batch =result->elements()[1].toTensor().toType(torch::kFloat32).to(at::kCPU);
    // set promise value
    for (unsigned int i = 0; i < promises.size(); i++) {
        torch::Tensor p = p_batch[i];
        torch::Tensor v = v_batch[i];
        std::vector<double> prob(p.data_ptr<float>(), p.data_ptr<float>() + p.numel());
        double value = v.item<float>();
        ActProbs_Value temp{ std::move(prob), std::move(value) };
        promises[i].set_value(std::move(temp));
    }
}
=======
version https://git-lfs.github.com/spec/v1
oid sha256:9ded2745f9b1f31d25dc4b524786b9983ad527e4a602da9cbb4c2fdd5792bf7b
size 2375
>>>>>>> 2673dac (pre)
