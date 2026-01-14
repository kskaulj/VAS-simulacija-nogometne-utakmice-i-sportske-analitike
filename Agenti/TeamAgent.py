# TeamAgent.py
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import ast

class TeamAgent(Agent):

    class RespondBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return

            try:
                req = ast.literal_eval(msg.body)
            except:
                return

            if req.get("type") != "REQUEST_ACTION":
                return

            minute = req["minute"]
            team = self.agent.team_name
            player = random.choice(self.agent.players)

            # odluke se donose na random, potencijalno mogu napravit da budu ovisne o nekom stanju
            action = random.choice(["pass", "pass", "pass", "shot", "shot", "foul"])

            xg_value = 0.0
            if action == "shot":
                xg_value = round(random.uniform(0.05, 0.85), 2)
                if random.random() < xg_value:
                    action = "goal"

            event = {"minute": minute, "team": team, "player": player, "action": action, "xG": xg_value}

            reply = Message(to=str(msg.sender))
            reply.body = str({"type": "ACTION", "event": event})
            await self.send(reply)

    async def setup(self):
        self.players = getattr(self, "players", [])
        self.team_name = getattr(self, "team_name", "Team")
        self.add_behaviour(self.RespondBehaviour())
        print(f"{self.team_name} started with {len(self.players)} players!")
