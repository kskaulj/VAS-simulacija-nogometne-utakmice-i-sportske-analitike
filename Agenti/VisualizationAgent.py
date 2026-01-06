from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import ast

class VisualizationAgent(Agent):
    async def setup(self):
        self.stats = {}
        self.prediction = "Waiting..."
        self.minute = 0
        self.add_behaviour(self.VizBehaviour())

    class VizBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                data = ast.literal_eval(msg.body)
                self.agent.stats = data["stats"]
                self.agent.prediction = data["prediction"]
                self.agent.minute = data["minute"]
