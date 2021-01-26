# Sapiogenesis
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![CodeFactor](https://www.codefactor.io/repository/github/edgecase963/sapiogenesis/badge?s=15c7abcfd2296a927216e6ab8461a81ceafcf994)](https://www.codefactor.io/repository/github/edgecase963/sapiogenesis)

![Logo](readme_media/splash-logo.jpg)

Sapiogenesis is a project designed to simulate the process of natural selection and evolution of not just physical bodies, but neural networks as well.

This allows organisms to adapt to their environment in ways previous evolution simulators did not. Simulated creatures not only become more physically suited to the environment they're placed in, but can learn from their experiences and make decisions based off memories of previous encounters.

In order to automate the process of learning and training these neural networks, dopamine values had to be programmed into each organism. Every creature has the capacity to feel pain, pleasure and even curiosity as well as boredom. These "feelings" are simulated, of course, but they are the backbone of what allows them to tell the difference between what's good and bad - what to avoid and what to pursue.

### A quick demo..
![Sapiogenesis Demo](readme_media/demo.gif)


To start Sapiogenesis:
```bash

# clone Sapiogenesis
git clone https://github.com/edgecase963/Sapiogenesis

cd Sapiogenesis

# Install requirements
pip3 install -r requirements.txt

python3.8 Sapiogenesis.py

```

A feature added in version 0.8 allows users to modify organisms or create new ones from scratch using the editor.

### Editor Demo
![Editor Demo](readme_media/editor_demo.gif)

To learn more, [check out the wiki](https://github.com/edgecase963/Sapiogenesis/wiki)


### Learning
Simulated organisms use what's called Reinforcement Learning in the field of AI and Machine Learning.

Based off certain variables - such as curiosity, stimulation and boredom - organisms will try new things, randomizing their actions in an attempt to gain experiences.
Based off a "reward" value (in this case, dopamine), organisms can determine how successful each action was and learn from it.

This process helps to refine what they learn and become more successful. Over time, they may learn to take advantage of the traits and cells they were born with. And, if successful enough, organisms can reproduce.


### Reproduction
Every time an organism reproduces, the offspring it creates are a mutated version of themselves. These mutations aren't just to the physical bodies of the organisms, but to the brains as well. You can set the severity of each mutation through the user interface.

This allows offspring to potentially become not just more physically adapted for their environment, but more intelligent.
