#!/usr/bin/env python3
# Q learning learning rate
alpha = 0.5

# Q learning discount rate
gamma = 0.9

# Epsilon initial
epsilon_initial = 0.35  # also constant with 0.2 is good

# Epsilon final
epsilon_final = 0.1

# Annealing timesteps
annealing_timesteps = 10000

# threshold
threshold = 1e-6