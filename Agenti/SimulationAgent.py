from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
import random

class SimulationAgent(Agent):
    class SimBehaviour(PeriodicBehaviour):
        async def run(self):
            minute = self.counter + 1
            team = random.choice(["Team A", "Team B"])
            r = random.random()

            event = {
                "minute": minute,
                "team": team,
                "type": None,
                "xg": 0.0
            }

            if r < 0.04:
                event["type"] = "goal"
                event["xg"] = round(random.uniform(0.2, 0.9), 2)
            elif r < 0.10:
                event["type"] = "shot"
                event["xg"] = round(random.uniform(0.05, 0.4), 2)
            elif r < 0.20:
                event["type"] = "foul"
            elif r < 0.55:
                event["type"] = "pass"
            else:
                self.counter += 1
                return

            msg = Message(to="analytics@localhost")
            msg.body = str(event)
            await self.send(msg)

            print(f"[SIM] {event}")

            self.counter += 1
            if self.counter >= 90:
                self.kill()

    async def setup(self):
        b = self.SimBehaviour(period=0.5)
        b.counter = 0
        self.add_behaviour(b)
