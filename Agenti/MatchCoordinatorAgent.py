from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
import ast
import random


class MatchCoordinatorAgent(Agent):
    async def setup(self):
        self.minute = 0

        # posjed lopte
        self.possession = "Team A"  
        self.last_possession_sent = None

        # mapiraj tim 
        self.team_jids = {
            "Team A": "teama@localhost",
            "Team B": "teamb@localhost",
        }

        self.add_behaviour(self.MatchLoop(period=1.0))
        print("Koordinator započinje!")

    class MatchLoop(PeriodicBehaviour):
        async def run(self):
            self.agent.minute += 1
            minute = self.agent.minute

            if minute > 90:
                print("[Koordinator] Utakmica je gotova!")
                self.kill()
                return

            
            pos_msg = Message(to="analytics@localhost")
            pos_msg.body = str({
                "type": "POSSESSION",
                "minute": minute,
                "team_in_possession": self.agent.possession
            })
            await self.send(pos_msg)
            self.agent.last_possession_sent = self.agent.possession

            
            team = self.agent.possession
            team_jid = self.agent.team_jids[team]

            req = Message(to=team_jid)
            req.body = str({"type": "REQUEST_ACTION", "minute": minute})
            await self.send(req)

           
            reply = await self.receive(timeout=1)
            if not reply:
                
                return

            try:
                data = ast.literal_eval(reply.body)
            except Exception:
                return

            if data.get("type") != "ACTION":
                return

            event = data.get("event")
            if not isinstance(event, dict):
                return

            
            event["minute"] = minute

            
            out = Message(to="analytics@localhost")
            out.body = str(event)
            await self.send(out)

            #pravila za posjed lopte
           
            action = event.get("action")

            if action == "foul":
                self.agent.possession = "Team B" if team == "Team A" else "Team A"
            elif action in ["shot", "goal"]:
                
                if random.random() < 0.7:
                    self.agent.possession = "Team B" if team == "Team A" else "Team A"
            else:
                
                if random.random() < 0.15:
                    self.agent.possession = "Team B" if team == "Team A" else "Team A"
