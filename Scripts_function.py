<<<<<<< HEAD
import os
from ctypes import windll
import win32api, win32con, win32gui
from PIL import Image, ImageGrab, ImageColor
import time
import numpy as np
from CppLibs import GomokuBoard, NeuralNet, MCTS
GRID_SIZE=15
def get_win_pos():
    handle=win32gui.FindWindow(0,"Yixin")
    if handle==0:
        raise Exception("please open Yixin first")
    else:
        (x, y, _, _) = win32gui.GetWindowRect(handle)
        x = x + 75
        y = y + 58
        win32gui.SendMessage(handle, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
        win32gui.SetForegroundWindow(handle)
        return x, y

def get_lastMove_pos(image1):
    #得到更新的结点值，x y大于等于0有效
    x1,y1=get_win_pos()
    image2=ImageGrab.grab((x1,y1,x1+480,y1+480))
    for x in range(0,GRID_SIZE):
        for y in range(0,GRID_SIZE):
            i=32*x+5
            j=32*y+5
            if image1.getpixel((i,j))!= image2.getpixel((i,j)):
                return x,y
    return -1,-1

def putChess(x,y):
    x1,y1=get_win_pos()
    i=x1+16+x*32
    j=y1+16+y*32
    i2, j2 = win32gui.GetCursorPos()
    windll.user32.SetCursorPos(i, j)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, i, j)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, i, j)
    windll.user32.SetCursorPos(i2,j2)

def TURN():
    x1, y1 = get_win_pos()
    image1=ImageGrab.grab((x1, y1, x1 + 480, y1 + 480))
    i=x1-35
    j=y1+242
    i2,j2=win32gui.GetCursorPos()
    windll.user32.SetCursorPos(i,j)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, i, j)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, i, j)
    windll.user32.SetCursorPos(i2,j2)
    while True:
        time.sleep(0.25)
        x1,y1=get_lastMove_pos(image1)
        if x1>=0 and y1>=0:
            break
    return x1,y1
def TURN_by_human():
    x1, y1 = get_win_pos()
    image1 = ImageGrab.grab((x1, y1, x1 + 480, y1 + 480))
    while True:
        time.sleep(0.25)
        x1,y1=get_lastMove_pos(image1)
        if x1>=0 and y1>=0:
            break
    return x1,y1

def get_pos(id):
    id=int(id)
    return id%GRID_SIZE,id//GRID_SIZE

def self_play():
    board = GomokuBoard()
    net1=NeuralNet("./Models/Libtorch/best_model.pt", True, 64)
    net2 = NeuralNet("./Models/Libtorch/best_model.pt", True, 64)
    player1 = MCTS(net1, 64, 1500, 225, 5, 3, 0)
    player2 = MCTS(net2, 64, 1500, 225, 5, 3, 0)
    restart()
    cnt=0
    while board.getBoardState() == board.NO_END:
        if cnt%2==0:
            plicyProbs = player1.getActionProbs(board, 0)
        else:
            plicyProbs = player2.getActionProbs(board, 0)
        aiMove = np.argmax(plicyProbs)
        board.executeMove(aiMove)
        player1.update(aiMove)
        player2.update(aiMove)
        x, y = get_pos(aiMove)
        putChess(x, y)
        board.display()
        cnt+=1

def start():
    board=GomokuBoard()
    #net=NeuralNet("./Models/Libtorch/best_model.pt", True, 64)
    net = NeuralNet("./Models/Libtorch/best_model.pt", True, 64)
    player=MCTS(net,64,2500,225,5,3,0)
    restart()
    cnt=0
    while board.getBoardState() == board.NO_END:
        if cnt%2==0:
            plicyProbs = player.getActionProbs(board, 0)
            aiMove = np.argmax(plicyProbs)
            board.executeMove(aiMove)
            player.update(aiMove)
            x, y = get_pos(aiMove)
            putChess(x, y)
            board.display()
        else:
            #x1, y1 = TURN()
            x1, y1 = TURN_by_human()
            board.executeMove(y1 * 15 + x1)
            player.update(y1 * 15 + x1)
            board.display()
        cnt+=1

def restart():
    x,y=get_win_pos()
    x-=75
    y-=58
    i1 = x+20
    j1 = y+40
    i2=x+50
    j2=y+60
    i3, j3 = win32gui.GetCursorPos()
    windll.user32.SetCursorPos(i1, j1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, i1, j1)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, i1, j1)
    windll.user32.SetCursorPos(i2, j2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, i2, j2)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, i2, j2)
    windll.user32.SetCursorPos(i3, j3)
    time.sleep(0.05)

if __name__ == "__main__":
    #self_play()
    start()
=======
version https://git-lfs.github.com/spec/v1
oid sha256:12501ffd6fe5b03f4aab27037cf114887940530202950572c10f556ff58ebd78
size 4409
>>>>>>> 2673dac (pre)
