from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import ast

class AnalyticsAgent(Agent):
    async def setup(self):
        self.minute = 0

        self.stats = {
            "Team A": {"goals":0, "shots":0, "fouls":0, "passes":0, "xg":0},
            "Team B": {"goals":0, "shots":0, "fouls":0, "passes":0, "xg":0}
        }

        self.player_stats = {
            "Team A": {},
            "Team B": {}
        }

        self.add_behaviour(self.AnalysisBehaviour())

    class AnalysisBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return

            event = ast.literal_eval(msg.body)
            team = event["team"]
            player = event["player"]
            self.agent.minute = event["minute"]

            if player not in self.agent.player_stats[team]:
                self.agent.player_stats[team][player] = {
                    "goals": 0,
                    "shots": 0,
                    "fouls": 0,
                    "passes": 0
                }

            if event["type"] == "goal":
                self.agent.stats[team]["goals"] += 1
                self.agent.stats[team]["xg"] += event["xg"]
                self.agent.player_stats[team][player]["goals"] += 1

            elif event["type"] == "shot":
                self.agent.stats[team]["shots"] += 1
                self.agent.stats[team]["xg"] += event["xg"]
                self.agent.player_stats[team][player]["shots"] += 1

            elif event["type"] == "foul":
                self.agent.stats[team]["fouls"] += 1
                self.agent.player_stats[team][player]["fouls"] += 1

            elif event["type"] == "pass":
                self.agent.stats[team]["passes"] += 1
                self.agent.player_stats[team][player]["passes"] += 1

            prediction = self.predict()

            msg_viz = Message(to="viz@localhost")
            msg_viz.body = str({
                "stats": self.agent.stats,
                "players": self.agent.player_stats,
                "prediction": prediction,
                "minute": self.agent.minute
            })
            await self.send(msg_viz)

        def predict(self):
            def score(t):
                s = self.agent.stats[t]
                return s["goals"]*3 + s["xg"] + s["shots"]*0.1

            a, b = score("Team A"), score("Team B")
            if a > b:
                return "Team A likely to win"
            elif b > a:
                return "Team B likely to win"
            return "Draw likely"
