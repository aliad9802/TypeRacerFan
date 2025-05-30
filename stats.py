import csv
import datetime

def write_session_csv(session_data, filename=None):
    """
    session_data: {
      'trials': [ {'word_no':…, 'word':…, 'time':…, 'wpm':…, 'accuracy':…}, … ],
      'total_score': int,
      'duration': float,       # seconds
      'max_combo': int
    }
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not filename:
        filename = f"session_{timestamp}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # header for trials
        w.writerow(["Word No", "Word", "Time (s)", "WPM", "Accuracy (%)"])
        for t in session_data['trials']:
            w.writerow([
                t['word_no'],
                t['word'],
                f"{t['time']:.2f}",
                f"{t['wpm']:.1f}",
                f"{t['accuracy']:.1f}"
            ])
        # blank line
        w.writerow([])
        # totals
        w.writerow(["Total Score", session_data['total_score']])
        w.writerow(["Session Duration (s)", f"{session_data['duration']:.2f}"])
        w.writerow(["Max Combo", session_data['max_combo']])
    return filename
