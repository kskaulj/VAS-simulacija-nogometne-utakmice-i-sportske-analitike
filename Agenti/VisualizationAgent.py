from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import ast

class VisualizationAgent(Agent):

    async def setup(self):
        self.current_data = {
            "stats": {
                "Team A": {"goals": 0, "shots": 0, "passes": 0, "fouls": 0, "xG": 0.0},
                "Team B": {"goals": 0, "shots": 0, "passes": 0, "fouls": 0, "xG": 0.0}
            },
            "events": [],
            "prediction": "Match starting...",
            "possession": {
                "current": "Team A",
                "minutes": {"Team A": 0, "Team B": 0},
                "timeline": []
            }
        }

        self.add_behaviour(self.ReceiveDataBehaviour())
        print("Visualization agent started!")

    class ReceiveDataBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return

            try:
                data = ast.literal_eval(msg.body)

                if "stats" in data:
                    self.agent.current_data["stats"] = data["stats"]

                if "latest_event" in data:
                    self.agent.current_data["events"].append(data["latest_event"])

                if "prediction" in data:
                    self.agent.current_data["prediction"] = data["prediction"]

                
                if "possession" in data and isinstance(data["possession"], dict):
                    self.agent.current_data["possession"] = data["possession"]

            except Exception:
                pass

    def get_current_data(self):
        return self.current_data
