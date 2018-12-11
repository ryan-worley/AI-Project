import random
import pickle
import collections
import Completed_FullBlackJack_Exact as ExactMDP
import numpy as np

# Abstract class: an RLAlgorithm performs reinforcement learning.  All it needs
# to know is the set of available actions to take.  The simulator (see
# simulate()) will call getAction() to get an action, perform the action, and
# then provide feedback (via incorporateFeedback()) to the RL algorithm, so it can adjust
# its parameters.
class RLAlgorithm:
    # Your algorithm will be asked to produce an action given a state.
    def getAction(self, state): raise NotImplementedError("Override me")

    # We will call this function when simulating an MDP, and you should update
    # parameters.
    # If |state| is a terminal state, this function will be called with (s, a,
    # 0, None). When this function is called, it indicates that taking action
    # |action| in state |state| resulted in reward |reward| and a transition to state
    # |newState|.
    def incorporateFeedback(self, state, action, reward, newState): raise NotImplementedError("Override me")

# An RL algorithm that acts according to a fixed policy |pi| and doesn't
# actually do any learning.
class FixedRLAlgorithm(RLAlgorithm):
    def __init__(self, pi): self.pi = pi

    # Just return the action given by the policy.
    def getAction(self, state): return self.pi[state]

    # Don't do anything: just stare off into space.
    def incorporateFeedback(self, state, action, reward, newState): pass

def betpolicy(lower, upper, loweramt, midamt, upperamt):
    policy = collections.defaultdict(float)
    for i in range(-10, 11):
        if i < lower:
            policy[i] = loweramt
        elif lower <= i <= upper:
            policy[i] = midamt
        else:
            policy[i] = upperamt
    return policy

def fixPlayerState(state):
    if state == '':
        return state
    if state == '21AD':
        return 21
    newState = list(state)
    if newState[-1].isdigit():
        return state + '*'
    for i, l in enumerate(state):
        if l.isalpha():
            newState.insert(i, '*')
            return ''.join(newState)

def fixDealerState(dealer, cards):
    if sum(cards) == 0:
        assert ValueError
    if dealer == '11A':
        return 11
    elif dealer:
        return int(dealer)
    else:
        return dealer

def adjustCount(count):
    if count > 10:
        return 10
    elif count < -10:
        return -10
    else:
        return count

# Perform |numTrials| of the following:
# On each trial, take the MDP |mdp| and an RLAlgorithm |rl| and simulates the
# RL algorithm according to the dynamics of the MDP.
# Each trial will run for at most |maxIterations|.
# Return the list of rewards that we get for each trial.
def simulate(mdp, rl, betPi, numTrials=1000, verbose=False, mincards=10, single_hand=False):
    def sample(probs):
        target = random.random()
        accum = 0
        for i, prob in enumerate(probs):
            accum += prob
            if accum >= target: return i
        raise Exception("Invalid probs: %s" % probs)


    totalRewards = []  # The rewards we get on each trial
    totalStates = []
    totalActions = []
    for trial in range(numTrials):
        state = mdp.startState()
        statesequence = [state]
        totalReward = 0
        rewardsequence = []
        actionsequence = []
        handreward = []
        hands = []
        handnum = 1
        print('Trial # {}:'.format(trial))
        while True:
            count = state[3]
            # Adjust true count so stays within limits
            count = adjustCount(count)

            if state[1] is None:
                if sum(state[2]) < mincards or single_hand:
                    break
                handnum += 1
                action = 'Begin'
                mdp.editBet(betPi[count])
                state = ('', '', state[2], state[3])
            else:
                action = rl.getAction((fixPlayerState(state[0]), fixDealerState(state[1], state[2]), count))

            # Choose random trans state
            transitions = mdp.succAndProbReward(state, action)
            i = sample([prob for _, prob, _ in transitions])

            # Pull out state, prob, reward from transition
            newState, prob, reward = transitions[i]

            # Add to sequence of items
            actionsequence.append(action)
            rewardsequence.append(reward)
            statesequence.append(newState)
            totalReward += reward
            state = newState

        if verbose:
            print("Trial {}, totalReward = {}, number of hands = {}, handReward = {}".format(trial, totalReward, handnum, totalReward/handnum))

        hands.append(handnum)
        totalRewards.append(totalReward)
        handreward.append(totalReward/handnum)
        totalStates.append(statesequence)
        totalActions.append(actionsequence)

    print('Total Average Reward is: {}'. format(sum(totalRewards)/len(totalRewards)))
    print('Total Average Hand Reward is: {}'. format(sum(handreward)/len(handreward)))
    return totalRewards, totalStates, totalActions, hands

def loadPolicy():
    policy = collections.defaultdict(str)
    counts = [i for i in range(-10, 11)]
    for count in counts:
        current_pi = pickle.load(open('./policy/' + 'Count {} Policy.pkl'.format(count), 'rb'))
        policy.update(current_pi)
    return policy

def main():
    pi = loadPolicy()
    rl = FixedRLAlgorithm(pi)
    trueMDP = ExactMDP.BlackjackMDP(multiplicity=8)
    bet_test = True
    if bet_test:
        betpi = betpolicy(0, 2, .5, 1, 5)
        tr, ts, ta, h = simulate(mdp=trueMDP, rl=rl, betPi=betpi, numTrials=1000, verbose=True)
    policy_test = False
    if policy_test:
        betpi = betpolicy(0, 2, 1, 1, 1)
        tr, ts, ta, h = simulate(mdp=trueMDP, rl=rl, betPi=betpi, numTrials=1000, verbose=True)

    actions = collections.defaultdict(int)
    # Create Action Log
    for action_sequence in ta:
        for action in action_sequence:
            actions[action] += 1

    count = collections.defaultdict(int)
    counts = []
    for state_seq in ts:
        for state in state_seq:
            count[state[3]] += 1
            counts.append(state[3])
    print(actions, count)
    mean = np.mean(counts)
    std = np.std(counts, ddof=1)
    print(counts)
    print(mean, std)




if __name__ == '__main__':
    main()
