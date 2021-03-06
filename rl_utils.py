from tqdm import tqdm
import numpy as np
import torch
import collections
import ENV_AGENT
import random

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = collections.deque(maxlen=capacity) 

    def add(self, state, action, reward, next_state, done): 
        self.buffer.append((state, action, reward, next_state, done)) 

    def sample(self, batch_size): 
        transitions = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done = zip(*transitions)
        return np.array(state), action, reward, np.array(next_state), done 

    def size(self): 
        return len(self.buffer)

def moving_average(a, window_size):
    cumulative_sum = np.cumsum(np.insert(a, 0, 0)) 
    middle = (cumulative_sum[window_size:] - cumulative_sum[:-window_size]) / window_size
    r = np.arange(1, window_size-1, 2)
    begin = np.cumsum(a[:window_size-1])[::2] / r
    end = (np.cumsum(a[:-window_size:-1])[::2] / r)[::-1]
    return np.concatenate((begin, middle, end))

def train_on_policy_agent(env, agent, num_episodes,max_steps):
    return_list = []
    done=False
    state = env.reset()
    for i_episode in range(num_episodes):
        episode_return = 0
        transition_dict = {'states': [], 'actions': [], 'next_states': [], 'rewards': [], 'dones': []}
        if done:
            state = env.reset()
            done = False
        step=0
        #print('NEW START')
        while not done and step<max_steps:
            step+=1
            action = agent.take_action(state)
            #print_state(env.env_agent)
            #print('action: \n',action)
            next_state, reward, done, _ = env.step(action)
            #print('reward: ',reward)
            transition_dict['states'].append(state)
            transition_dict['actions'].append(action)
            transition_dict['next_states'].append(next_state)
            transition_dict['rewards'].append(reward)
            transition_dict['dones'].append(done)
            state = next_state
            episode_return += reward
        return_list.append(episode_return)
        agent.update(transition_dict)
        if (i_episode+1) % 10 == 0:
            print('episode:{}, reward:{}'.format(i_episode+1,np.mean(return_list[-10])))
    return return_list

def print_state(env:ENV_AGENT.ENV_AGENT):
    print('pro_index: ',env.pro_index)
    print('speed: ',env.processor_speed)
    print('loc: ',env.processor_location)
    print('sub: \n',env.subtask_location)

def train_off_policy_agent(env, agent, num_episodes, replay_buffer, minimal_size, batch_size):
    return_list = []
    for i_episode in range(num_episodes):
        episode_return = 0
        state = env.reset()
        done = False
        while not done:
            action = agent.take_action(state)
            next_state, reward, done, _ = env.step(action)
            replay_buffer.add(state, action, reward, next_state, done)
            state = next_state
            episode_return += reward
            if replay_buffer.size() > minimal_size:
                b_s, b_a, b_r, b_ns, b_d = replay_buffer.sample(batch_size)
                transition_dict = {'states': b_s, 'actions': b_a, 'next_states': b_ns, 'rewards': b_r, 'dones': b_d}
                agent.update(transition_dict)
        return_list.append(episode_return)
        if (i_episode+1) % 10 == 0:
            print('episode:{}, reward:{}'.format(i_episode+1,np.mean(return_list[-10])))
    return return_list


def compute_advantage(gamma, lmbda, td_delta):
    td_delta = td_delta.detach().numpy()
    advantage_list = []
    advantage = 0.0
    for delta in td_delta[::-1]:
        advantage = gamma * lmbda * advantage + delta
        advantage_list.append(advantage)
    advantage_list.reverse()
    return torch.tensor(np.concatenate(advantage_list,axis=0), dtype=torch.float)
                