import asyncio
import threading
from SimulationAgent import SimulationAgent
from AnalyticsAgent import AnalyticsAgent
from VisualizationAgent import VisualizationAgent
from dashboard import run_dashboard

async def main():
    viz = VisualizationAgent("viz@localhost", "password")
    analytics = AnalyticsAgent("analytics@localhost", "password")
    sim = SimulationAgent("simulation@localhost", "password")

    await viz.start()
    await analytics.start()
    await sim.start()

    await asyncio.sleep(1)  # osigurava stabilan start

    threading.Thread(
        target=run_dashboard,
        args=(viz,),
        daemon=True
    ).start()

    while sim.is_alive():
        await asyncio.sleep(1)

    # uredno gašenje
    await analytics.stop()
    await viz.stop()

asyncio.run(main())
