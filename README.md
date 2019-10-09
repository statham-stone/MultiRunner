# MultiRunner说明文档

这是一个进程级别的python并行框架，可用于深度学习调参等任务，可通过 pip install MultiRunner 安装

**注意，本包的使用极度简洁，原代码完全无需改动，使用本包的时候，包含import语句在内，仅需加入四行代码。**

如果你遇到了以下问题之一，你可能需要这个包：

- 你是一个机器学习调参侠，你在一台主机上安装了多个GPU，或者你有多台共享硬盘的主机（节点，aws，hpc等），你需要以不同的参数运行一个函数多次，该函数针对每个参数返回一个结果（你可能想知道最好的那个结果所对应的参数，没错，我说的就是深度炼丹）。你想让这些主机/GPU并行地为你跑程序，但是你懒得手动一个个输入命令，且**由于不同的主机/GPU运算能力不同，完成不同任务所需要的时间也不同，你不知道该如何为不同的节点分配不同的任务量**，你不愿意坐在电脑前等着程序运行结束，也不想一个个手动输入命令

- 你有一台普通电脑，你需要以不同的参数运行一个函数多次并得到结果，你想尽力并行运行这个函数以加快实验速度，但是你不想学习Multiprocessing库

先看一个例子，你原来的代码可能是这样的：
```
# old_run.py

def train_a_model(batch_size,hidden_layer_number,learning_rate):
    #your code here
    return accuracy

for batch_size in [16,64,256]:
    for hidden_layer_number in [1,2]:
        for learning_rate in [0.001,0.01,0.1]:
            print batch_size,hidden_layer_number,learning_rate
            my_result = train_a_model(batch_size,hidden_layer_number,learning_rate)
            print my_result
```

现在它可以是这样：


```
# new_run.py

def train_a_model(batch_size,hidden_layer_number,learning_rate):
    #your code here
    return accuracy

from MultiRunner import MultiRunner

a=MultiRunner()
a.generate_ini([[16,64,256], [1,2], [0.001,0.01,0.1]])#注意这里，所有的参数列表要最后用一个list或者tuple括起来
a.run(train_a_model)
```

**注意**：修改后的代码可以在多台共享硬盘的主机上（或同一台电脑的不同GPU上）同时跑，多个进程会并行地跑不同的实验，一个进程跑完某个实验之后将以文件格式保存该实验结果并立即运行下一个没跑过的实验。我们已经在代码中做了充分的多进程冲突处理（全部是封装好的）

**你只要需要在多个节点的同一个目录下分别运行 python new_run.py 即可**

运行该代码后，最先运行该代码的进程会创建./ini目录，并在其中以文件的格式保存参数用于进程同步，以刚刚的代码为例，该文件夹内会有3\*2\*3=18个文件，文件以pickle格式存储，分明命名为0\_to\_run, 1\_to\_run ...... 17\_to\_run

实验过程中，每个正在运行的参数对应的文件后缀将被更改为XX\_running，以5\_to\_run为例，该参数对应的实验过程中，5\_to\_run将被改名为5\_running，若该实验成功运行完毕，实验结果以pickle文件格式成功存储于./results/5，5\_running将再次被重命名为5\_finished。

代码可以处理实验过程中的错误情况，如果某个参数的实验中出现了错误，该参数对应的文件XX\_running会自动回滚为XX\_to\_run，之后该进程将会选择另一个参数进行实验，当一个进程合计错误次数达到一定值的时候，该进程将退出，默认值是5，该值可以通过对象创建时候的max_error_times参数进行设定。

# 进阶内容
- 函数find_best_gpu可以返回当前空闲的gpu id
- 为最大化地优化实验速度，如果某进程运行完一个实验后，进行下一个实验参数选择的时候发现所有的参数都已经实验完毕或者实验正在运行的，该进程会随机选择一个正在运行的实验参数运行，这样设计的目的是避免出现以下情况：A, B主机/GPU运行速度很快，C主机/GPU运行速度很慢，C选取了一个参数慢慢运行，A, B虽然没有任务但是无法为C分担，实验速度被C拖慢。本设计中，如果遇到上述情况，A, B在运行完自己的实验后都会运行C的实验，并在C运行完毕前得到实验结果，因此提高了实验速度。但是，代码也会存在实验结果已经全部得出但是仍有进程在运行的问题。
- 以上的叙述中，我们仅以每个主机/GPU上仅运行一个进程为例。**事实上，假设我们有两台共享硬盘的主机，每台主机上有3个GPU，每个GPU上同时运行了4个进程，这2\*3\*4=24个进程同时运行，我们的代码也无需做任何更改。**

有任何问题都可以直接提issue，也可以发邮件联系我。

**欢迎给Star，欢迎fork，欢迎提新需求。**
