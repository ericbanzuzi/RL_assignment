#!/usr/bin/env python3
import random
import numpy as np

from agent import Fish
from communicator import Communicator
from shared import SettingLoader


class FishesModelling:
    def init_fishes(self, n):
        fishes = {}
        for i in range(n):
            fishes["fish" + str(i)] = Fish()
        self.fishes = fishes


class PlayerController(SettingLoader, Communicator):
    def __init__(self):
        SettingLoader.__init__(self)
        Communicator.__init__(self)
        self.space_subdivisions = 10
        self.actions = None
        self.action_list = None
        self.states = None
        self.init_state = None
        self.ind2state = None
        self.state2ind = None
        self.alpha = 0
        self.gamma = 0
        self.episode_max = 300

    def init_states(self):
        ind2state = {}
        state2ind = {}
        count = 0
        for row in range(self.space_subdivisions):
            for col in range(self.space_subdivisions):
                ind2state[(col, row)] = count
                state2ind[count] = [col, row]
                count += 1
        self.ind2state = ind2state
        self.state2ind = state2ind

    def init_actions(self):
        self.actions = {
            "left": (-1, 0),
            "right": (1, 0),
            "down": (0, -1),
            "up": (0, 1)
        }
        self.action_list = list(self.actions.keys())

    def allowed_movements(self):
        self.allowed_moves = {}
        for s in self.ind2state.keys():
            self.allowed_moves[self.ind2state[s]] = []
            if s[0] < self.space_subdivisions - 1:
                self.allowed_moves[self.ind2state[s]] += [1]
            if s[0] > 0:
                self.allowed_moves[self.ind2state[s]] += [0]
            if s[1] < self.space_subdivisions - 1:
                self.allowed_moves[self.ind2state[s]] += [3]
            if s[1] > 0:
                self.allowed_moves[self.ind2state[s]] += [2]

    def player_loop(self):
        pass


class PlayerControllerHuman(PlayerController):
    def player_loop(self):
        """
        Function that generates the loop of the game. In each iteration
        the human plays through the keyboard and send
        this to the game through the sender. Then it receives an
        update of the game through receiver, with this it computes the
        next movement.
        :return:
        """

        while True:
            # send message to game that you are ready
            msg = self.receiver()
            if msg["game_over"]:
                return


def epsilon_greedy(Q,
                   state,
                   all_actions,
                   current_total_steps=0,
                   epsilon_initial=1,
                   epsilon_final=0.2,
                   anneal_timesteps=10000,
                   eps_type="constant"):

    if eps_type == 'constant':
        epsilon = epsilon_final
        # ADD YOUR CODE SNIPPET BETWEEN EX 4.1
        # Implement the epsilon-greedy algorithm for a constant epsilon value
        # Use epsilon and all input arguments of epsilon_greedy you see fit
        # It is recommended you use the np.random module
        P = np.random.uniform(0, 1)
        if P < (1-epsilon):
            action = np.nanargmax(Q[state])
        else:
            # action = all_actions[np.random.randint(len(all_actions))]
            action = np.random.choice(all_actions, 1, p=[1/len(all_actions) for _ in range(len(all_actions))])[0]
        # ADD YOUR CODE SNIPPET BETWEEN EX 4.1

    elif eps_type == 'linear':
        # ADD YOUR CODE SNIPPET BETWEENEX  4.2
        # Implemenmt the epsilon-greedy algorithm for a linear epsilon value
        # Use epsilon and all input arguments of epsilon_greedy you see fit
        # use the ScheduleLinear class
        # It is recommended you use the np.random module
        scheduler = ScheduleLinear(anneal_timesteps, epsilon_final, epsilon_initial)
        e_t = scheduler.value(current_total_steps)
        P = np.random.uniform(0, 1)
        if P < e_t:
            action = np.random.choice(all_actions, 1, p=[1/len(all_actions) for _ in range(len(all_actions))])[0]
            # action = all_actions[np.random.randint(len(all_actions))]
        else:
            action = np.nanargmax(Q[state])
        # ADD YOUR CODE SNIPPET BETWEENEX  4.2

    else:
        raise "Epsilon greedy type unknown"

    return action


def alpha_decay(alpha_initial,
                alpha_final,
                current_total_steps,
                anneal_timesteps):
    scheduler = ScheduleLinear(anneal_timesteps, alpha_final, alpha_initial)
    alpha_t = scheduler.value(current_total_steps)
    return alpha_t


class PlayerControllerRL(PlayerController, FishesModelling):
    def __init__(self):
        super().__init__()

    def player_loop(self):
        # send message to game that you are ready
        self.init_actions()
        self.init_states()
        self.alpha = self.settings.alpha
        self.gamma = self.settings.gamma
        self.epsilon_initial = self.settings.epsilon_initial
        self.epsilon_final = self.settings.epsilon_final
        self.annealing_timesteps = self.settings.annealing_timesteps
        self.threshold = self.settings.threshold
        self.episode_max = self.settings.episode_max
        self.alpha_final = 0.001
        self.alpha_initial = self.settings.alpha
        self.N = 5

        q = self.q_learning()

        # compute policy
        policy = self.get_policy(q)

        # send policy
        msg = {"policy": policy, "exploration": False}
        self.sender(msg)

        msg = self.receiver()
        print("Q-learning returning")
        return

    def q_learning(self):
        ns = len(self.state2ind.keys())
        na = len(self.actions.keys())
        discount = self.gamma
        lr = self.alpha
        # initialization
        self.allowed_movements()
        # ADD YOUR CODE SNIPPET BETWEEN EX. 2.1
        # Initialize a numpy array with ns state rows and na state columns with float values from 0.0 to 1.0.
        Q = np.random.rand(ns, na)
        # ADD YOUR CODE SNIPPET BETWEEN EX. 2.1

        for s in range(ns):
            list_pos = self.allowed_moves[s]
            for i in range(4):
                if i not in list_pos:
                    Q[s, i] = np.nan

        Q_old = Q.copy()

        diff = np.infty
        end_episode = False

        init_pos_tuple = self.settings.init_pos_diver
        init_pos = self.ind2state[(init_pos_tuple[0], init_pos_tuple[1])]
        episode = 0

        R_total = 0
        current_total_steps = 0
        steps = 0
        highest_Rs = []
        highest_R_found = -np.inf

        # ADD YOUR CODE SNIPPET BETWEEN EX. 2.3
        # Change the while loop to incorporate a threshold limit, to stop training when the mean difference
        # in the Q table is lower than the threshold
        while episode <= self.episode_max and diff > self.threshold:
            # and not self.similar_Rs(highest_Rs, highest_R_found)
            s_current = init_pos
            R_total = 0
            steps = 0
            highest_R_episode = -np.inf
            while not end_episode:
                # selection of action
                list_pos = self.allowed_moves[s_current]

                # ADD YOUR CODE SNIPPET BETWEEN EX 5
                # Use the epsilon greedy algorithm to retrieve an action
                action = epsilon_greedy(Q, s_current, list_pos, current_total_steps, self.epsilon_initial,
                                        self.epsilon_final, self.annealing_timesteps, 'constant')
                # ADD YOUR CODE SNIPPET BETWEEN EX 5

                # compute reward
                action_str = self.action_list[action]
                msg = {"action": action_str, "exploration": True}
                self.sender(msg)

                # wait response from game
                msg = self.receiver()
                R = msg["reward"]
                R_total += R
                s_next_tuple = msg["state"]
                end_episode = msg["end_episode"]
                s_next = self.ind2state[s_next_tuple]

                # ADD YOUR CODE SNIPPET BETWEEN EX. 2.2
                # Implement the Bellman Update equation to update Q
                max_act_s_next = np.nanargmax(Q[s_next])
                Q[s_current, action] += self.alpha*(R + self.gamma*Q[s_next, max_act_s_next] - Q[s_current, action])
                # ADD YOUR CODE SNIPPET BETWEEN EX. 2.2

                s_current = s_next
                current_total_steps += 1
                steps += 1
            highest_R_episode = np.max([highest_R_episode, R_total])
            # ADD YOUR CODE SNIPPET BETWEEN EX. 2.3
            # Compute the absolute value of the mean between the Q and Q-old
            diff = np.abs(np.nanmean(Q-Q_old))
            # ADD YOUR CODE SNIPPET BETWEEN EX. 2.3
            Q_old[:] = Q
            print("Episode: {}, Steps {}, Diff: {:6e}, Total Reward: {}, Total Steps {}"
                  .format(episode, steps, diff, R_total, current_total_steps))
            # if len(highest_Rs) < self.N:
            #     highest_Rs.append(highest_R_episode)
            # else:
            #     del highest_Rs[0]
            #     highest_Rs.append(highest_R_episode)

            episode += 1
            end_episode = False
            # highest_R_found = np.max([highest_R_episode, highest_R_found])
            # self.alpha = alpha_decay(self.alpha_initial, self.alpha_final,
            #                          current_total_steps, self.annealing_timesteps)
            self.alpha = np.max([0.01, 0.99*self.alpha])

        return Q

    def get_policy(self, Q):
        max_actions = np.nanargmax(Q, axis=1)
        policy = {}
        list_actions = list(self.actions.keys())
        for n in self.state2ind.keys():
            state_tuple = self.state2ind[n]
            policy[(state_tuple[0],
                    state_tuple[1])] = list_actions[max_actions[n]]
        return policy

    def similar_Rs(self, R_list, highest_R_found):
        if len(R_list) < self.N or highest_R_found != 11:
            return False

        epsilon = 0.2
        similar_Rs = np.all(np.abs(np.array(R_list)-np.mean(R_list)) < epsilon)
        similar_to_highest = np.all(np.abs(np.array(R_list)-highest_R_found) < epsilon)
        return similar_to_highest and similar_Rs


class PlayerControllerRandom(PlayerController):
    def __init__(self):
        super().__init__()

    def player_loop(self):

        self.init_actions()
        self.init_states()
        self.allowed_movements()
        self.episode_max = self.settings.episode_max

        n = self.random_agent()

        # compute policy
        policy = self.get_policy(n)

        # send policy
        msg = {"policy": policy, "exploration": False}
        self.sender(msg)

        msg = self.receiver()
        print("Random Agent returning")
        return

    def random_agent(self):
        ns = len(self.state2ind.keys())
        na = len(self.actions.keys())
        init_pos_tuple = self.settings.init_pos_diver
        init_pos = self.ind2state[(init_pos_tuple[0], init_pos_tuple[1])]
        episode = 0
        R_total = 0
        steps = 0
        current_total_steps = 0
        end_episode = False
        # ADD YOUR CODE SNIPPET BETWEEN EX. 1.2
        # Initialize a numpy array with ns state rows and na state columns with zeros
        # ADD YOUR CODE SNIPPET BETWEEN EX. 1.2

        while episode <= self.episode_max:
            s_current = init_pos
            R_total = 0
            steps = 0
            while not end_episode:
                # all possible actions
                possible_actions = self.allowed_moves[s_current]

                # ADD YOUR CODE SNIPPET BETWEEN EX. 1.2
                # Chose an action from all possible actions and add to the counter of actions per state
                action = None
                # ADD YOUR CODE SNIPPET BETWEEN EX. 1.2

                action_str = self.action_list[action]
                msg = {"action": action_str, "exploration": True}
                self.sender(msg)

                # wait response from game
                msg = self.receiver()
                R = msg["reward"]
                s_next_tuple = msg["state"]
                end_episode = msg["end_episode"]
                s_next = self.ind2state[s_next_tuple]
                s_current = s_next
                R_total += R
                current_total_steps += 1
                steps += 1

            print("Episode: {}, Steps {}, Total Reward: {}, Total Steps {}".
                  format(episode, steps, R_total, current_total_steps))
            episode += 1
            end_episode = False

        return n

    def get_policy(self, Q):
        nan_max_actions_proxy = [None for _ in range(len(Q))]
        for _ in range(len(Q)):
            try:
                nan_max_actions_proxy[_] = np.nanargmax(Q[_])
            except:
                nan_max_actions_proxy[_] = np.random.choice([0, 1, 2, 3])

        nan_max_actions_proxy = np.array(nan_max_actions_proxy)

        assert nan_max_actions_proxy.all() == nan_max_actions_proxy.all()

        policy = {}
        list_actions = list(self.actions.keys())
        for n in self.state2ind.keys():
            state_tuple = self.state2ind[n]
            policy[(state_tuple[0],
                    state_tuple[1])] = list_actions[nan_max_actions_proxy[n]]
        return policy


class ScheduleLinear(object):
    def __init__(self, schedule_timesteps, final_p, initial_p=1.0):
        self.schedule_timesteps = schedule_timesteps
        self.final_p = final_p
        self.initial_p = initial_p

    def value(self, t):
        # ADD YOUR CODE SNIPPET BETWEEN EX 4.2
        # Return the annealed linear value
        e_delta = self.final_p - self.initial_p  # -0.499
        e_t = self.initial_p + e_delta*(t/self.schedule_timesteps)
        return e_t
        # ADD YOUR CODE SNIPPET BETWEEN EX 4.2

