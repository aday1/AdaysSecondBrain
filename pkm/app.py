from datetime import datetime
from sqlalchemy import func
from flask import jsonify, request

@app.route('/save_anxiety_data', methods=['POST'])
def save_anxiety_data():
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        # Get table info before attempting insert
        with db.engine.connect() as conn:
            result = conn.execute("PRAGMA table_info(anxiety_logs);")
            columns = [row[1] for row in result]
            print(f"Available columns: {columns}")  # Debug log

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        try:
            # Print the actual SQL query that would be executed
            new_entry = AnxietyLog(
                timestamp=datetime.strptime(f"{data['date']} {data['timeStarted']}", '%Y-%m-%d %H:%M'),
                suds_score=int(data.get('sudsScore', 0)),
                social_isolation=int(data.get('socialIsolation', 0)),
                insufficient_self_control=int(data.get('insufficientSelfControl', 0)),
                subjugation=int(data.get('subjugation', 0)),
                negativity=int(data.get('negativity', 0)),
                unrelenting_standards=int(data.get('unrelentingStandards', 0)),  # Match camelCase from frontend
                trigger_id=int(data['trigger']) if data.get('trigger') and data['trigger'] != 'new' else None,
                coping_strategy_id=int(data['copingStrategy']) if data.get('copingStrategy') and data['copingStrategy'] != 'new' else None,
                effectiveness=int(data.get('effectiveness', 0)),
                duration_minutes=int(data.get('durationMinutes', 0)),
                notes=data.get('notes', '')
            )
            print(f"SQL Query: {str(db.session.query(AnxietyLog))}")  # Add SQL logging
            print(f"Created entry object: {vars(new_entry)}")  # Debug log
            
            db.session.add(new_entry)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Data saved successfully'}), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 400
            
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}')}), 500

@app.route('/get_anxiety_data')
def get_anxiety_data():
    try:
        logs = AnxietyLog.query.order_by(AnxietyLog.timestamp).all()
        
        log_data = [{
            'timestamp': log.timestamp.isoformat(),
            'suds': log.suds_score,
            'social': log.social_isolation,
            'control': log.insufficient_self_control,
            'subjugation': log.subjugation,
            'negativity': log.negativity,
            'standards': log.unrelenting_standards,
            'trigger': log.trigger.name if log.trigger else '',
            'strategy': log.coping_strategy.name if log.coping_strategy else '',
            'effectiveness': log.effectiveness,
            'duration': log.duration_minutes
        } for log in logs]
        
        return jsonify({
            'timestamps': [log['timestamp'] for log in log_data],
            'suds': [log['suds'] for log in log_data],
            'social': [log['social'] for log in log_data],
            'control': [log['control'] for log in log_data],
            'subjugation': [log['subjugation'] for log in log_data],
            'negativity': [log['negativity'] for log in log_data],
            'standards': [log['standards'] for log in log_data],
            'logs': log_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_current_datetime')
def get_current_datetime():
    now = datetime.now()
    return jsonify({
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M')
    })