"""
This part of code is the reinforcement learning brain, which is a brain of the agent.
All decisions are made in here.
Policy Gradient, Reinforcement Learning.
View more on my tutorial page: https://morvanzhou.github.io/tutorials/
Using:
Tensorflow: 1.0
gym: 0.8.0
"""

import numpy as np
import tensorflow as tf

# reproducible
np.random.seed(1)
tf.set_random_seed(1)


class PolicyGradient:
    def __init__(
            self,
            n_actions,
            n_features,
            learning_rate=0.01,
            reward_decay=0.95,
            output_graph=False,
    ):
        self.n_actions = n_actions	#一个动作用 一个 n_actions 维向量 表示
        self.n_features = n_features	#一个状态observation用 一个 n_features 维向量 表示
        self.lr = learning_rate
        self.gamma = reward_decay

        self.ep_obs, self.ep_as, self.ep_rs = [], [], []	#分别存放 s a r 的队列

        self._build_net()		# 建立 a = πΘ(s) 的具体实现网络

        self.sess = tf.Session()

        if output_graph:
            # $ tensorboard --logdir=logs
            # http://0.0.0.0:6006/
            # tf.train.SummaryWriter soon be deprecated, use following
            tf.summary.FileWriter("logs/", self.sess.graph)

        self.sess.run(tf.global_variables_initializer())	# 注意是先_build_net(),注册了各色各样的var,然后再initial

    def _build_net(self):
        with tf.name_scope('inputs'):
            self.tf_obs = tf.placeholder(tf.float32, [None, self.n_features], name="observations")	#放 s 队列的 占位符
            self.tf_acts = tf.placeholder(tf.int32, [None, ], name="actions_num")
            self.tf_vt = tf.placeholder(tf.float32, [None, ], name="actions_value")
        # fc1
        layer = tf.layers.dense(			# tensorflow 的 全连接层模型,简单说就是一般的 m维入,n维出的神经元层
            inputs=self.tf_obs,				# batch 个 M 维输入变量
            units=10,					# units数=n 相当于 输出 batch 个 n维输出 变量 
            activation=tf.nn.tanh,  # tanh activation   使用tach 的激励函数
            kernel_initializer=tf.random_normal_initializer(mean=0, stddev=0.3), # W 权值初始化量
            bias_initializer=tf.constant_initializer(0.1),	# b 初始化量
            name='fc1'					#层 名称
        )
        # fc2
        all_act = tf.layers.dense(
            inputs=layer,				
            units=self.n_actions,
            activation=None,
            kernel_initializer=tf.random_normal_initializer(mean=0, stddev=0.3),
            bias_initializer=tf.constant_initializer(0.1),
            name='fc2'
        )

	#通过 softmax 获得类似 one-hot特性的向量,至此self.all_act_prob 就建立了 a = πΘ(s) 的关系
        self.all_act_prob = tf.nn.softmax(all_act, name='act_prob')  # use softmax to convert to probability

	#接下来这段是 policy gradient 的误差算式子
        with tf.name_scope('loss'):
            # to maximize total reward (log_p * R) is to minimize -(log_p * R), and the tf only have minimize(loss)
	    # 这里使用的是 交叉墒,代替 log(policy),而不是正统的 log(policy)
            neg_log_prob = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=all_act, labels=self.tf_acts)   # this is negative log of chosen action
            # or in this way:
            # neg_log_prob = tf.reduce_sum(-tf.log(self.all_act_prob)*tf.one_hot(self.tf_acts, self.n_actions), axis=1)
            loss = tf.reduce_mean(neg_log_prob * self.tf_vt)  # reward guided loss

        with tf.name_scope('train'):
            self.train_op = tf.train.AdamOptimizer(self.lr).minimize(loss)	#梯度下降法缩小 误差!!

    def choose_action(self, observation):
        #显然每次挂入一个4维 observation,不是多个!!
        prob_weights = self.sess.run(self.all_act_prob, feed_dict={self.tf_obs: observation[np.newaxis, :]})	
	# random.choice 这句很多学问, range()得到的是一个一维数组,但后面一句也行!!
        action = np.random.choice(range(prob_weights.shape[1]), p=prob_weights.ravel())  # select action w.r.t the actions prob
	# by william debug and learn 
        #action = np.random.choice(prob_weights.shape[1], p=prob_weights.ravel())  # select action w.r.t the actions prob
        #print(prob_weights)
        #print(prob_weights.shape[1])
        #print(prob_weights.ravel())
        #print(range(prob_weights.shape[1]))
        #print(action)
        #input("Enter your input: ")
        return action

    def store_transition(self, s, a, r):
        self.ep_obs.append(s)
        self.ep_as.append(a)
        self.ep_rs.append(r)

    def learn(self):
        # discount and normalize episode reward
        discounted_ep_rs_norm = self._discount_and_norm_rewards()

        # train on episode
        self.sess.run(self.train_op, feed_dict={
             self.tf_obs: np.vstack(self.ep_obs),  # shape=[None, n_obs]
             self.tf_acts: np.array(self.ep_as),  # shape=[None, ]
             self.tf_vt: discounted_ep_rs_norm,  # shape=[None, ]
        })

        self.ep_obs, self.ep_as, self.ep_rs = [], [], []    # empty episode data	清空 这次episode的 内容!!
        return discounted_ep_rs_norm

    def _discount_and_norm_rewards(self):	#这里就开始涉及马尔科夫模型 discounted_reward  G(t) = r + γ G(t+1) 
        # discount episode rewards
        discounted_ep_rs = np.zeros_like(self.ep_rs)      # 构造一个矩阵W_update，其维度与矩阵W一致，并为其初始化为全0
        running_add = 0
        for t in reversed(range(0, len(self.ep_rs))):	# reversed 表示 i 是倒数着来的
            running_add = running_add * self.gamma + self.ep_rs[t]
            discounted_ep_rs[t] = running_add

        # normalize episode rewards	获得 每一step 的 G(t) 后,正规化 G(t) 方便计算
        discounted_ep_rs -= np.mean(discounted_ep_rs)	# ( G(t) - 平均值 ) / 标准差
        discounted_ep_rs /= np.std(discounted_ep_rs)	
        return discounted_ep_rs
'''
学习分析笔记!!
根据算法定义:
function REINFORCE
    Initialise θ arbitrarily
    for each episode { s1,a1,r2,...,sT−1,aT−1,rT }∼πθ do
        for t = 1 to T−1 do
            θ ← θ + α * ∇θ ( logπθ(st,at)vt )
        end for
    end for
    returnθ
end function
	
policy gradient 有几个重点
1,行为策略 a = πθ(s)
  在这里 在s状态 通过策略 πθ(s) 得到动作 a, 
  相应地 πθ(s,a) 的得到是 在s状态,获得动作a 对应的策略,表现为在s状态,获得动作几率
2,奖励 vt / v(t) / Gt / G(t) / R(sa) 有好多称谓,但都是同个概念,都是马尔科夫模型的一个概念
  当前 s 执行了a 得到 的奖励  v(t) = r + v(t+1)
  r是直接奖励,  v(t+1)是 下个 s 执行了a 得到 的奖励
  这个奖励模型拥有前瞻性意义!!,表示了这一步的奖励 拥有了多少 导致episode成功结束 贡献价值
  即隐约告诉我们 是否更靠近成功的结束
3 根据 算法定义 我们的  loss 可以设置为 j(θ) =E[ ∑ -logπθ(st,at)vt ]
					    t
  logπθ(st,at) 与 πθ(s,a) 意义一样, 即在s状态,获得动作a 对应的策略,表现为在s状态,获得动作几率
  使用 logπθ(st,at) 是为了跟好计算
  假若 完全锻炼的 策略, loss 很小, 意味这 任一 timestep (即t) 都 选择了相当正确的行为a
   1, 大多数情况, 
      比如 t = 10, 执行了 a = πθ(s) 的 a , 得到很高的 vt (更近成功终点), πθ(s,a)几乎等于1
      然后 -logπθ(st,at) ≈ 0 所以 -logπθ(s,a)vt ≈ 0,表示对 loss 几乎没有贡献
      表示这一步使用 a 无比正确的策略,不用修正策略
   2, 几乎 有 1 - e_greedy 甚至更小 概率出现的情况 
      比如 t = 78, 执行了 a = πθ(s) 以外的 a1,但得到 很小的 Vt (更远离成功终点), πθ(s,a)比如等于0.1
      然后 -logπθ(st,at) ≈ 1 所以 -logπθ(s,a)vt ≈ vt, 表示 表示对 loss 几乎没有贡献
      表示这一步使用 a1 是错误的,所以策略还是正确的,不用修正策略 πθ(s),或者修正很小内容	
   2, 极少数情况, 
      比如 t = 49, 执行了 a = πθ(s) 以外的 a1 , 也得到很高的 vt (更近成功终点), πθ(s,a)等于0.3
      然后 logπθ(st,at) ≈ -0.5,即 -logπθ(st,at) ≈ 0.5 所以 -logπθ(s,a)vt >0,(例如 = 10)
      表示 这一步虽然使用了策略外的一步,但是得到很大的vt(更近成功终点),
      表示在这个 s 执行的 a = πθ(s) 的策略值得怀疑, 应该有所改变,应该更偏向 a1
4 实际情况 我们 没有使用 logπθ(s,a) 这个模块, 而是使用 all_act 和 self.tf_acts 的交叉熵来代替
  logπθ(s,a) 与 交叉熵 虽然算法不一样,但意义是一样的:
      当执行的行为是远离策略时, 值比较大, 
      当执行的行为等于策略导出的,值=0
  之所以这么替代,是因为 不知当如何构造 logπθ(s,a),相反,建立交叉熵比较简单
  all_act 是每个时刻t,策略导出 a = πθ(s) 组成的 数组
  self.tf_acts 是每个时刻t,真正执行的 a 组成的 数组
  计算 每个 t 得到 交叉熵,就等于比对那刻 执行的行为 是否等于 策略导出的,
  是则等于0,非则是一个比较大的值
  所以可完全取代了 logπθ(s,a)
5 然后这里学习 的策略参数θ 对应的 其实就是 策略网络里的 fc1 fc2 里的 W b
  而 这里的 self.tf_vt 是 每一刻t 执行的实际的 a 得到 奖励, 
  而不是 策略算出的行为a 对应的奖励
'''

