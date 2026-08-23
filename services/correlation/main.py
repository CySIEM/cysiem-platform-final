import json
from pathlib import Path

from api.incident_api import analyze_incidents


def main() -> None:
    data_path = Path(__file__).resolve().parent / "sample_data" / "alerts.json"
    with data_path.open("r", encoding="utf-8") as handle:
        alerts = json.load(handle)

    result = analyze_incidents(alerts)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
