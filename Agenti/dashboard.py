from flask import Flask, render_template_string, jsonify
import plotly.graph_objs as go
import plotly.utils
import json

app = Flask(__name__)
viz_agent = None


def run_dashboard(agent):
    global viz_agent
    viz_agent = agent
    app.run(debug=False, port=5000, use_reloader=False)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MAS Soccer Simulation — Live Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

    <style>
        :root{
            --bg-main: #0b1320;
            --bg-top: #13233d;
            --panel: #111827;
            --panel-2: #0f1a2b;

            --accent-blue: #1e90ff;
            --accent-green: #2ecc71;
            --accent-yellow: #facc15;

            --text: #e5e7eb;
            --muted: #9ca3af;

            --stroke: rgba(255,255,255,0.08);
            --grid: rgba(255,255,255,0.06);

            --shadow: 0 12px 30px rgba(0,0,0,0.55);
        }

        * { box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Inter, Arial, sans-serif;
            margin: 0;
            padding: 18px;
            color: var(--text);
            background:
                radial-gradient(circle at top, var(--bg-top) 0%, var(--bg-main) 60%),
                linear-gradient(180deg, rgba(46,204,113,0.06), rgba(0,0,0,0));
        }

        .header {
            text-align: center;
            margin-bottom: 18px;
        }

        .title-row{
            display:flex;
            align-items:center;
            justify-content:center;
            gap:12px;
            margin-bottom: 6px;
        }

        .badge{
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding: 6px 10px;
            border: 1px solid var(--stroke);
            border-radius: 999px;
            background: rgba(17,24,39,0.65);
            box-shadow: var(--shadow);
            font-size: 12px;
            letter-spacing: .12em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .badge .dot{
            width:8px; height:8px;
            border-radius:50%;
            background: var(--accent-green);
            box-shadow: 0 0 12px rgba(46,204,113,0.8);
        }

        h1 {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0;
            color: white;
        }

        .score {
            font-size: 76px;
            font-weight: 950;
            letter-spacing: 6px;
            margin: 10px 0 6px 0;
            color: white;
            text-shadow: 0 0 26px rgba(30,144,255,0.55);
        }

        .prediction {
            font-size: 20px;
            padding: 12px 20px;
            border-radius: 14px;
            display: inline-block;
            margin: 10px 0 0 0;
            border: 1px solid var(--stroke);
            background: linear-gradient(
                90deg,
                rgba(30,144,255,0.16),
                rgba(46,204,113,0.14)
            );
            backdrop-filter: blur(8px);
            box-shadow: var(--shadow);
        }

        .meta-row{
            display:flex;
            gap: 12px;
            justify-content:center;
            flex-wrap: wrap;
            margin-top: 14px;
        }

        .pill {
            display:inline-flex;
            align-items:center;
            gap:10px;
            padding: 10px 14px;
            border-radius: 14px;
            border: 1px solid var(--stroke);
            background: rgba(17,24,39,0.65);
            box-shadow: var(--shadow);
            min-width: 220px;
            justify-content: center;
        }

        .pill .label{
            color: var(--muted);
            font-size: 12px;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        .pill .value{
            font-weight: 800;
            font-size: 16px;
            color: white;
        }

        .value.blue { color: var(--accent-blue); text-shadow: 0 0 14px rgba(30,144,255,0.35); }
        .value.green { color: var(--accent-green); text-shadow: 0 0 14px rgba(46,204,113,0.35); }
        .value.yellow { color: var(--accent-yellow); text-shadow: 0 0 14px rgba(250,204,21,0.25); }

        .charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-top: 16px;
        }

        .chart {
            background: linear-gradient(180deg, var(--panel), var(--panel-2));
            padding: 14px 14px 6px 14px;
            border-radius: 18px;
            box-shadow: var(--shadow);
            border: 1px solid var(--stroke);
            overflow: hidden;
        }

        .chart-title{
            font-size: 12px;
            letter-spacing: .14em;
            text-transform: uppercase;
            color: var(--muted);
            margin: 2px 0 10px 0;
            display:flex;
            justify-content: space-between;
            align-items:center;
        }

        .chart-title .tag{
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid var(--stroke);
            background: rgba(0,0,0,0.18);
            color: var(--muted);
            font-size: 11px;
        }

        .full-width { grid-column: 1 / -1; }

        /* Mobile */
        @media(max-width: 900px){
            .charts{ grid-template-columns: 1fr; }
            .pill{ min-width: 0; width: 100%; }
            .score{ font-size: 62px; }
        }
    </style>
</head>

<body>
    <div class="header">
        <div class="title-row">
            <span class="badge"><span class="dot"></span> Live Simulation</span>
            <h1>MAS Soccer Dashboard</h1>
            <span class="badge">Multi-Agent System</span>
        </div>

        <div class="score" id="score">0 - 0</div>
        <div class="prediction" id="prediction">Prediction</div>

        <div class="meta-row">
            <div class="pill">
                <span class="label">Possession</span>
                <span class="value yellow" id="possession-current">Team A</span>
            </div>

            <div class="pill">
                <span class="label">xG Team A</span>
                <span class="value blue" id="xg-a">0.00</span>
            </div>

            <div class="pill">
                <span class="label">xG Team B</span>
                <span class="value green" id="xg-b">0.00</span>
            </div>
        </div>
    </div>

    <div class="charts">
        <div class="chart">
            <div class="chart-title">Goals <span class="tag">Scoreline</span></div>
            <div id="goals-chart"></div>
        </div>

        <div class="chart">
            <div class="chart-title">Expected Goals <span class="tag">xG</span></div>
            <div id="xg-chart"></div>
        </div>

        <div class="chart">
            <div class="chart-title">Match Statistics <span class="tag">Volume</span></div>
            <div id="stats-chart"></div>
        </div>

        <div class="chart">
            <div class="chart-title">Possession Timeline <span class="tag">Flow</span></div>
            <div id="possession-chart"></div>
        </div>

        <div class="chart full-width">
            <div class="chart-title">Events Timeline <span class="tag">Actions</span></div>
            <div id="events-chart"></div>
        </div>
    </div>

    <script>
        // ===== Sport Broadcast Theme (Plotly) =====
        const THEME = {
            TEAM_A: '#1e90ff',
            TEAM_B: '#2ecc71',
            MOMENT: '#facc15',
            GRID: 'rgba(255,255,255,0.06)',
            FONT: '#e5e7eb',
            MUTED: '#9ca3af'
        };

        const baseLayout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: THEME.FONT, family: 'Inter, Segoe UI, Arial, sans-serif' },
            margin: { l: 40, r: 20, t: 40, b: 40 },
            xaxis: {
                gridcolor: THEME.GRID,
                zerolinecolor: THEME.GRID,
                tickfont: { color: THEME.MUTED },
                titlefont: { color: THEME.MUTED }
            },
            yaxis: {
                gridcolor: THEME.GRID,
                zerolinecolor: THEME.GRID,
                tickfont: { color: THEME.MUTED },
                titlefont: { color: THEME.MUTED }
            },
            legend: { font: { color: THEME.MUTED } }
        };

        function updateDashboard() {
            fetch('/api/data')
                .then(r => r.json())
                .then(data => {
                    // Score
                    document.getElementById('score').textContent =
                        data.score_a + ' - ' + data.score_b;

                    // Prediction
                    document.getElementById('prediction').textContent = data.prediction;

                    // Possession text
                    document.getElementById('possession-current').textContent = data.possession_current;

                    // xG values
                    document.getElementById('xg-a').textContent = data.xg_a.toFixed(2);
                    document.getElementById('xg-b').textContent = data.xg_b.toFixed(2);

                    // Goals chart
                    Plotly.react('goals-chart', [{
                        type: 'bar',
                        x: ['Team A', 'Team B'],
                        y: [data.score_a, data.score_b],
                        marker: { color: [THEME.TEAM_A, THEME.TEAM_B] },
                        text: [data.score_a, data.score_b],
                        textposition: 'outside'
                    }], {
                        ...baseLayout,
                        title: { text: 'GOALS', font: { size: 14, color: THEME.MUTED } },
                        height: 260,
                        yaxis: { ...baseLayout.yaxis, title: 'Goals' }
                    }, {displayModeBar: false, responsive: true});

                    // xG chart
                    Plotly.react('xg-chart', [{
                        type: 'bar',
                        x: ['Team A', 'Team B'],
                        y: [data.xg_a, data.xg_b],
                        marker: { color: [THEME.TEAM_A, THEME.TEAM_B] },
                        text: [data.xg_a.toFixed(2), data.xg_b.toFixed(2)],
                        textposition: 'outside'
                    }], {
                        ...baseLayout,
                        title: { text: 'EXPECTED GOALS (xG)', font: { size: 14, color: THEME.MUTED } },
                        height: 260,
                        yaxis: { ...baseLayout.yaxis, title: 'xG' }
                    }, {displayModeBar: false, responsive: true});

                    // Stats chart
                    Plotly.react('stats-chart', [
                        {
                            name: 'Team A',
                            type: 'bar',
                            x: ['Goals', 'Shots', 'Passes', 'Fouls'],
                            y: [data.stats_a.goals, data.stats_a.shots, data.stats_a.passes, data.stats_a.fouls],
                            marker: { color: THEME.TEAM_A }
                        },
                        {
                            name: 'Team B',
                            type: 'bar',
                            x: ['Goals', 'Shots', 'Passes', 'Fouls'],
                            y: [data.stats_b.goals, data.stats_b.shots, data.stats_b.passes, data.stats_b.fouls],
                            marker: { color: THEME.TEAM_B }
                        }
                    ], {
                        ...baseLayout,
                        title: { text: 'MATCH STATISTICS', font: { size: 14, color: THEME.MUTED } },
                        height: 260,
                        barmode: 'group'
                    }, {displayModeBar: false, responsive: true});

                    // Possession timeline (broadcast style step line)
                    if (data.possession_timeline.length > 0) {
                        const x = data.possession_timeline.map(p => p.minute);
                        const y = data.possession_timeline.map(p => p.team === 'Team A' ? 1 : 0);

                        Plotly.react('possession-chart', [{
                            x: x,
                            y: y,
                            mode: 'lines+markers',
                            line: {
                                shape: 'hv',
                                width: 4,
                                color: THEME.MOMENT
                            },
                            marker: {
                                size: 8,
                                color: THEME.MOMENT
                            },
                            hovertext: data.possession_timeline.map(p => `Minute ${p.minute}: ${p.team}`),
                            hoverinfo: 'text'
                        }], {
                            ...baseLayout,
                            title: { text: 'BALL POSSESSION TIMELINE', font: { size: 14, color: THEME.MUTED } },
                            height: 260,
                            yaxis: {
                                ...baseLayout.yaxis,
                                tickvals: [0, 1],
                                ticktext: ['Team B', 'Team A'],
                                title: 'Team in possession'
                            },
                            xaxis: {
                                ...baseLayout.xaxis,
                                title: 'Minute',
                                range: [0, 90]
                            }
                        }, {displayModeBar: false, responsive: true});
                    }

                    // Events timeline (from backend, but we "theme" layout colors)
                    const ev = data.events_chart;
                    ev.layout = ev.layout || {};
                    ev.layout.paper_bgcolor = 'rgba(0,0,0,0)';
                    ev.layout.plot_bgcolor = 'rgba(0,0,0,0)';
                    ev.layout.font = { color: THEME.FONT, family: 'Inter, Segoe UI, Arial, sans-serif' };
                    ev.layout.xaxis = ev.layout.xaxis || {};
                    ev.layout.yaxis = ev.layout.yaxis || {};
                    ev.layout.xaxis.gridcolor = THEME.GRID;
                    ev.layout.yaxis.gridcolor = THEME.GRID;
                    ev.layout.xaxis.tickfont = { color: THEME.MUTED };
                    ev.layout.yaxis.tickfont = { color: THEME.MUTED };
                    ev.layout.height = 360;
                    ev.layout.margin = { l: 70, r: 20, t: 50, b: 50 };
                    ev.layout.title = { text: 'EVENTS TIMELINE', font: { size: 14, color: THEME.MUTED } };

                    Plotly.react('events-chart', ev.data, ev.layout, {displayModeBar: false, responsive: true});
                });
        }

        setInterval(updateDashboard, 1000);
        updateDashboard();
    </script>
</body>
</html>
"""



@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/api/data')
def get_data():
    if viz_agent is None:
        return jsonify({"error": "Not ready"})

    data = viz_agent.get_current_data()
    stats = data["stats"]
    events = data["events"]
    prediction = data.get("prediction", "Calculating...")

    # graf za posjed lopte
    pos = data.get("possession", {})
    pos_current = pos.get("current", "Team A")
    pos_minutes = pos.get("minutes", {"Team A": 0, "Team B": 0})
    pos_timeline = pos.get("timeline", [])


    # događanja
    team_a_events = [e for e in events if e.get("team") == "Team A"]
    team_b_events = [e for e in events if e.get("team") == "Team B"]

    events_fig = go.Figure()

    if team_a_events:
        events_fig.add_trace(go.Scatter(
            x=[e["minute"] for e in team_a_events],
            y=[e["action"] for e in team_a_events],
            mode='markers',
            name='Team A',
            marker=dict(size=10, color="#a8bbcf"),
            text=[
                f"{e.get('player', '')}" +
                (f" (xG: {e.get('xG', 0):.2f})" if e.get('xG', 0) > 0 else "")
                for e in team_a_events
            ],
            hoverinfo='text+x+y'
        ))

    if team_b_events:
        events_fig.add_trace(go.Scatter(
            x=[e["minute"] for e in team_b_events],
            y=[e["action"] for e in team_b_events],
            mode='markers',
            name='Team B',
            marker=dict(size=10, color="#7a5f62"),
            text=[
                f"{e.get('player', '')}" +
                (f" (xG: {e.get('xG', 0):.2f})" if e.get('xG', 0) > 0 else "")
                for e in team_b_events
            ],
            hoverinfo='text+x+y'
        ))

    events_fig.update_layout(
        title='Events Timeline',
        xaxis_title='Minute',
        yaxis_title='Action',
        height=400
    )

    return jsonify({
        'score_a': stats['Team A']['goals'],
        'score_b': stats['Team B']['goals'],
        'xg_a': stats['Team A']['xG'],
        'xg_b': stats['Team B']['xG'],
        'stats_a': stats['Team A'],
        'stats_b': stats['Team B'],
        'prediction': prediction,
        'possession_current': pos_current,
        'possession_minutes_a': pos_minutes.get("Team A", 0),
        'possession_minutes_b': pos_minutes.get("Team B", 0),
        'possession_timeline': pos_timeline,

        'events_chart': json.loads(plotly.utils.PlotlyJSONEncoder().encode(events_fig))
    })
