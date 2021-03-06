"""
Policy Gradient, Reinforcement Learning.
The cart pole example
View more on my tutorial page: https://morvanzhou.github.io/tutorials/
Using:
Tensorflow: 1.0
gym: 0.8.0
"""

import gym
from RL import PolicyGradient
import matplotlib.pyplot as plt

DISPLAY_REWARD_THRESHOLD = 400000  # renders environment if total episode reward is greater then this threshold
RENDER = False  # rendering wastes time

env = gym.make('CartPole-v0')
env.seed(1)     # reproducible, general Policy gradient has high variance
env = env.unwrapped

print(env.action_space)
print(env.observation_space)
print(env.observation_space.high)
print(env.observation_space.low)

#打印出 向量 的维度大小!!
print(env.action_space.n)	#一个动作用 一个 env.action_space.n 维向量 表示
print(env.observation_space.shape[0])	#一个状态observation用 一个 env.observation_space.shape[0] 维向量 表示

RL = PolicyGradient(
    n_actions=env.action_space.n,
    n_features=env.observation_space.shape[0],
    learning_rate=0.02,
    reward_decay=0.99,
    # output_graph=True,
)


for i_episode in range(3000):
#for i_episode in range(3):

    observation = env.reset()	#每个episode开始回到初始状态s 状态s 记录在 observation

    while True:
        if RENDER: env.render()	#当打开开关时才开始 游戏过程

        action = RL.choose_action(observation)	# a = πΘ(s) 根据策略选动作 这里action 只有0和1 两个值

        observation_, reward, done, info = env.step(action) #执行a 得到 新的 s' r  和其他信息(动作是否完成done，其他消息),

        RL.store_transition(observation, action, reward) # 保存当前 s a r 

        if done:	#一个episode 结束时才执行的更新过程!!

            #以下一段是用于监察模型训练进度,与模型训练过程无关!!
            ep_rs_sum = sum(RL.ep_rs)
            if 'running_reward' not in globals():    # python 内置函数 记录所有全局量,这里是 running_reward 第一次初始化= ep_rs_sum
                running_reward = ep_rs_sum
            else:
                running_reward = running_reward * 0.99 + ep_rs_sum * 0.01	#这里的 running_reward 只不过是做累加记录,并不是模型里的 r 角色
            if running_reward > DISPLAY_REWARD_THRESHOLD: RENDER = True     # rendering running_reward 只方便用于观察训练进度,
            print("episode:", i_episode, "  reward:", int(running_reward))

            #训练模型
            vt = RL.learn()

            if i_episode == 70:
                plt.plot(vt)    # plot the episode vt
                plt.xlabel('episode steps')
                plt.ylabel('normalized state-action value')
                plt.show()
            break

        observation = observation_	#把 s' 传给为下一阶段的 s



'''

增强学习有几个基本概念：

(1)     agent：智能体，也就是机器人，你的代码本身。

(2)     environment：环境，也就是游戏本身，openai gym提供了多款游戏，也就是提供了多个环境。

(3)     action：行动，比如玩超级玛丽，向上向下等动作。

(4)     state：状态，每次智能体做出行动，环境会相应地做出反应，返回一个状态和奖励。

(5)     reward：奖励：根据游戏规则的得分。智能体不知道怎么才能得分，它通过不断地尝试来理解游戏规则，比如它在这个状态做出向上的动作，得分，那么下一次它处于这个环境状态，就倾向于做出向上的动作。

 技术分享

OpenAI Gym由两部分组成：

    gym开源库：测试问题的集合。当你测试增强学习的时候，测试问题就是环境，比如机器人玩游戏，环境的集合就是游戏的画面。这些环境有一个公共的接口，允许用户设计通用的算法。
    OpenAI Gym服务。提供一个站点（比如对于游戏cartpole-v0：https://gym.openai.com/envs/CartPole-v0）和api，允许用户对他们的测试结果进行比较。

 

gym的代码在这上面：https://github.com/openai/gym

gym的核心接口是Env，作为统一的环境接口。Env包含下面几个核心方法：

1、reset(self):重置环境的状态，返回观察。

2、step(self,action):推进一个时间步长，返回observation，reward，done，info

3、render(self,mode=’human’,close=False):重绘环境的一帧。默认模式一般比较友好，如弹出一个窗口。
'''

