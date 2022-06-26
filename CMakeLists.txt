<<<<<<< HEAD
cmake_minimum_required(VERSION 3.5.1)
project(CppLibs)
set(CMAKE_CXX_STANDARD 17)
#set libtorch path
set(CMAKE_PREFIX_PATH "/home/sheep/Libs/libtorch")
#set pybind11 path
set(pybind11_DIR "/home/sheep/Libs/pybind11")
#set python version
set(PYBIND11_PYTHON_VERSION 3.8)
set(CMAKE_BUILD_TYPE "Release")
find_package(Torch REQUIRED)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${TORCH_CXX_FLAGS}")
include_directories(${TORCH_INCLUDE_DIRS})
link_libraries(${TORCH_LIBRARIES})
add_subdirectory(${pybind11_DIR} pybind11.out)
pybind11_add_module(CppLibs CppLibs.cpp APV_MCTS.cpp GomokuBoard.cpp NeuralNet.cpp)
=======
version https://git-lfs.github.com/spec/v1
oid sha256:b54b7228f8effe3abcacdf4caf183453223311cd2af0088883d302186c579224
size 600
>>>>>>> 2673dac (pre)
