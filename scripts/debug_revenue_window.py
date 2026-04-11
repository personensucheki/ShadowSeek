from app import create_app
from app.extensions import db
from app.models.revenue import RevenueEvent
from datetime import datetime, timedelta

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        today = datetime.utcnow().date()
        days = [today - timedelta(days=index) for index in range(13, -1, -1)]
        start_date = days[0]
        end_date = days[-1] + timedelta(days=1)
        events = RevenueEvent.query.filter(
            RevenueEvent.captured_at >= start_date,
            RevenueEvent.captured_at < end_date
        ).all()
        print(f"Gefundene Events im Zeitraum {start_date} bis {end_date}: {len(events)}")
        for e in events:
            print(f"{e.captured_at} | {e.platform} | {e.username} | {e.estimated_revenue}")
