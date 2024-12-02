import logging
from flask import jsonify, render_template, request
from datetime import datetime, timedelta
import json
from .models import SubMood
from . import db

@app.route('/log_sub_mood', methods=['POST'])
def log_sub_mood():
    try:
        data = request.form
        new_mood = SubMood(
            date=datetime.strptime(data['mood_date'], '%Y-%m-%d').date(),
            time=datetime.strptime(data['mood_time'], '%H:%M').time(),
            mood_level=int(data['mood_level']),
            energy_level=int(data['energy_level']),
            activity=data['activity'],
            notes=data['notes']
        )
        db.session.add(new_mood)
        db.session.commit()
        app.logger.info(f"Mood logged successfully: {new_mood.__dict__}")
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Error logging mood: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/metrics')
def metrics():
    try:
        # Get date range for the past week
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Initialize default values
        chart_data = {
            'dates': [],
            'moods': [],
            'energies': [],
            'notes': []
        }
        
        debug_data = {
            'total_entries': 0,
            'latest_entry': None,
            'daily_counts': [],
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Fetch mood data for the past week
        moods = db.session.query(
            SubMood.date,
            db.func.avg(SubMood.mood_level).label('avg_mood'),
            db.func.avg(SubMood.energy_level).label('avg_energy')
        ).filter(
            SubMood.date.between(start_date, end_date)
        ).group_by(SubMood.date).all()

        # Format data for charts
        chart_data.update({
            'dates': [m.date.strftime('%Y-%m-%d') for m in moods],
            'moods': [float(m.avg_mood) for m in moods],
            'energies': [float(m.avg_energy) for m in moods]
        })

        # Fetch recent notes
        recent_notes = db.session.query(SubMood).order_by(
            SubMood.date.desc(),
            SubMood.time.desc()
        ).limit(10).all()

        # Convert notes to serializable format
        notes_data = [{
            'date': note.date.strftime('%Y-%m-%d'),
            'time': note.time.strftime('%H:%M'),
            'activity': note.activity or '',
            'notes': note.notes or '',
            'mood_level': note.mood_level,
            'energy_level': note.energy_level
        } for note in recent_notes]

        # Update debug data
        debug_data.update({
            'total_entries': db.session.query(SubMood).count(),
            'latest_entry': notes_data[0] if notes_data else None,
            'daily_counts': [
                [d.strftime('%Y-%m-%d'), c] 
                for d, c in db.session.query(
                    SubMood.date, 
                    db.func.count(SubMood.id)
                ).group_by(SubMood.date).all()
            ]
        })

        app.logger.info(f"Chart data: {json.dumps(chart_data)}")
        app.logger.info(f"Debug data: {json.dumps(debug_data)}")

        return render_template('metrics.html',
                             chart_data=chart_data,
                             notes=notes_data,
                             debug_data=debug_data,
                             selected_date=end_date.strftime('%Y-%m-%d'),
                             current_time=datetime.now().strftime('%H:%M'))
                             
    except Exception as e:
        app.logger.error(f"Error in metrics route: {str(e)}")
        return render_template('metrics.html', 
                             error=str(e),
                             chart_data={'dates':[], 'moods':[], 'energies':[], 'notes':[]},
                             debug_data={'error': str(e)},
                             selected_date=datetime.now().strftime('%Y-%m-%d'),
                             current_time=datetime.now().strftime('%H:%M'))