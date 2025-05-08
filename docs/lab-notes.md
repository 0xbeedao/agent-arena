# Lab Notes

## 2025-05-07 08:04:10

I haven't been keeping good lab notes on this project. Let's start now.

I have been approaching this project with several goals:

- enjoy programming in Python again
- use mature, testable libraries as backbone
- make everything trackable and discoverable
- deterministic, except for the LLM responses

As I've developed it, I've had several major refactors, due to breakthroughs in
my understanding of several of the base techs. Dependency_injector is a powerful
library & pattern, and I'm leaning on it heavily while learning to use it effectively.

Currently, I am wrapping up a major refactor of injected controller methods1 into controller classes.
Doing so lets me avoid manual wiring, and more importantly, regularizes the responses.

I need to finish fixing the tests, then the fixture loader.

At that point, I want to write some integration test/experiments to prove out the Request [[state-machine]].

Next, I think I will work on getting a polling loop running for the queue

Then, I'd like to test doing an Arena setup with features.

## 2025-05-07 08:23:22

Yes! Got all the tests fixed.

## 2025-05-07 12:44:40

I note that somehow I reverted my dropping of LiteQueue.  OK, I think that's a quick one.

I'll remove LiteQueue, since I am already doing all that in the Jobs table, and I want to, for stateful analysis later.

## 2025-05-08

Removed LiteQueue, somehow I had a detached head on Git, thanks for the Local-history plugin, I recovered it.

Pushed out to GitHub repo [agent-arena](https://github.com/0xbeedao/agent-arena?tab=readme-ov-file)

All tests pass

