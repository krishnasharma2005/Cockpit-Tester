from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import datetime
import csv
from switch_reader import OPCReader

app = Flask(__name__)
opc = OPCReader()
opc.connect()

previous_node_values = {}

with open("test_plan.json") as f:
    data = json.load(f)
    all_switches = data["switches"]

flat_tests = []
for switch in all_switches:
    for test in switch.get("tests", []):
        test["switch_name"] = switch["name"]
        test["panel"] = switch["panel"]
        test["passed"] = False  # Shared flag across all modes
        test["Type"] = test.get("type", "input")
        #test["is_write_output"] = test["Type"] == "output" and "WriteNode" in test.get("Expected", {})
        flat_tests.append(test)

def group_tests_by_panel_ordered():
    panels = {}
    for switch in all_switches:
        panel = switch["panel"]
        for test in switch.get("tests", []):
            test_id = test["Id"]
            test["switch_name"] = switch["name"]
            test["panel"] = panel
            test["Type"] = test.get("type", "input")
            #test["is_write_output"] = test["Type"] == "output" and "WriteNode" in test.get("Expected", {})

            if panel not in panels:
                panels[panel] = []
            panels[panel].append(test)
    return panels

# CSV log
LOG_FILE = "test_log.csv"
def log_result(test_id, current, expected, match):
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(), test_id, current, expected, match
        ])

@app.route("/")
def index():
    panels = group_tests_by_panel_ordered()
    total_tests = len(flat_tests)
    total_passed = len([t for t in flat_tests if t["passed"]])
    return render_template("index.html", panels=panels, total_tests=total_tests, total_passed=total_passed)

@app.route("/panel/<panel_name>")
def panel_view(panel_name):
    mode = request.args.get("mode", "manual")
    panels = group_tests_by_panel_ordered()
    if panel_name not in panels:
        return "Panel not found", 404
    tests = panels[panel_name]
    total = len(tests)
    passed = len([t for t in tests if t["passed"]])
    return render_template("panel.html", panel=panel_name, tests=tests, total=total, passed=passed, mode=mode)

@app.route("/read/<test_id>")
def read_test_value(test_id):
    test = next((t for t in flat_tests if t["Id"] == test_id), None)
    if not test:
        return jsonify({"status": "error", "message": "Test ID not found"}), 404

    node_id = test["OPCNode"]
    current_value = opc.read_node(node_id)
    expected = test.get("Expected", {})

    match = False
    if "ChangeTo" in expected:
        match = expected["ChangeTo"] == "any" or str(current_value) == str(expected["ChangeTo"])
    elif "ChangeDirection" in expected:
        expected_direction = expected["ChangeDirection"]
        previous_value = previous_node_values.get(node_id)
        if previous_value is not None:
            try:
                curr = float(current_value)
                prev = float(previous_value)
                match = (curr > prev if expected_direction == "increase" else curr < prev)
            except ValueError:
                match = False
        previous_node_values[node_id] = current_value

    if match:
        test["passed"] = True

    log_result(test["Id"], current_value, expected, match)

    return jsonify({"current": current_value, "expected": expected, "match": match})

@app.route("/reset/<panel_name>")
def reset_panel(panel_name):
    mode = request.args.get("mode", "manual")
    for test in flat_tests:
        if test["panel"] == panel_name:
            test["passed"] = False
    return redirect(f"/panel/{panel_name}?mode={mode}")

@app.route("/reset-all")
def reset_all():
    for test in flat_tests:
        test["passed"] = False
    return redirect(url_for("index"))

@app.route("/get_overall_progress")
def get_overall_progress():
    total = len(flat_tests)
    passed = len([t for t in flat_tests if t["passed"]])
    return jsonify({"progress": int((passed/total)*100) if total > 0 else 0})

@app.route("/next-panel")
def next_panel():
    current = request.args.get("current")
    panels = list(group_tests_by_panel_ordered().keys())
    if current in panels:
        idx = panels.index(current)
        for next_panel in panels[idx+1:]:
            remaining = [t for t in flat_tests if t["panel"] == next_panel and not t["passed"]]
            if remaining:
                return jsonify({"next": next_panel})
    return jsonify({"next": None})

@app.route("/test-all")
def test_all():
    panels = group_tests_by_panel_ordered()
    for name, tests in panels.items():
        if any(not t["passed"] for t in tests):
            return redirect(url_for("panel_view", panel_name=name, mode="auto"))
    return redirect(url_for("index"))

@app.route("/confirm/<test_id>", methods=["POST"])
def confirm_output_test(test_id):
    test = next((t for t in flat_tests if t["Id"] == test_id), None)
    if test:
        test["passed"] = True
        log_result(test["Id"], "user_confirmed", test["Expected"], True)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route("/output-step", methods=["POST"])
def output_step():
    data = request.json
    test_id = data.get("test_id")
    phase = data.get("phase")  # "on" or "off"

    test = next((t for t in flat_tests if t["Id"] == test_id), None)
    if not test:
        return jsonify({"success": False}), 404

    expected = test.get("Expected", {})
    node_id = expected.get("WriteNode")
    value = expected.get("WriteOn") if phase == "on" else expected.get("WriteOff")

    print(f"[DEBUG] /output-step: test_id={test_id}, phase={phase}")
    print(f"[DEBUG] Node: {node_id}, Value: {value}")

    if node_id and value is not None:
        success = opc.write_node(node_id, value)
        return jsonify({"success": success})
    return jsonify({"success": False})
    
@app.route("/panel_progress/<panel_name>")
def panel_progress(panel_name):
    panels = group_tests_by_panel_ordered()
    if panel_name not in panels:
        return jsonify({"error": "Panel not found"}), 404
    tests = panels[panel_name]
    total = len(tests)
    passed = len([t for t in tests if t.get("passed")])
    progress_percent = int((passed / total) * 100) if total > 0 else 0
    return jsonify({
        "total": total,
        "passed": passed,
        "progress_percent": progress_percent
    })


if __name__ == '__main__':
    try:
        with open(LOG_FILE, 'x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "test_id", "current", "expected", "match"])
    except FileExistsError:
        pass

    app.run(host="0.0.0.0", port=5000)
