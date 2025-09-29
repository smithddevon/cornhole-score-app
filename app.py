import mysql.connector
import os
from flask import Flask, flash, render_template, request, jsonify, session, redirect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__)

# Set secret key for session
app.secret_key = os.getenv("SECRET_KEY")

def get_db_cursor():
    try:
        if os.getenv("INSTANCE_CONNECTION_NAME"):
            db = mysql.connector.connect(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                unix_socket=f"/cloudsql/{os.getenv('INSTANCE_CONNECTION_NAME')}"
            )
        else:
            db = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
        return db, db.cursor(dictionary=True)

    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None, None


def insert_game_data(team1_name, team1_score, team2_name, team2_score, winner):
    """Insert game data into the database"""
    print("insert_game_data called")  # Debug log

    if winner is None:
        print("Winner cannot be null. Ignoring game data insertion.")
        return
    
    try:
        db, cursor = get_db_cursor()
        if not db or not cursor:
            return
        
        # Debug log
        print(f"Data being inserted: {team1_name}, {team1_score}, {team2_name}, {team2_score}, {winner}")

        # Insert game data into the database
        cursor.execute(
            """
            INSERT INTO scores (team1_name, team1_score, team2_name, team2_score, winner)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (team1_name, team1_score, team2_name, team2_score, winner)
        )
        db.commit()  # Commit the transaction to save changes
        print("Database insert committed.")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@app.route("/")
def index():
    """Show ScoreKeeper"""
    return render_template("submit_team_names.html")

@app.route("/submit_team_names", methods=["GET", "POST"])
def submit_team_names():
    if request.method == "POST":
        # Clear session for new game
        session.clear()

        # Get team names
        team1_name = request.form.get("team1")
        team2_name = request.form.get("team2")

        # Initialize session data
        session["team1_name"] = team1_name
        session["team2_name"] = team2_name
        session["team1_score"] = 0
        session["team2_score"] = 0
        session["winner"] = None

        # Redirect to score counter route
        return redirect("/score_counter")

@app.route('/score_counter', methods=["GET"])
def score_counter():
    team1_name = session.get("team1_name", "Team 1")
    team2_name = session.get("team2_name", "Team 2")
    team1_score = session.get("team1_score", 0)
    team2_score = session.get("team2_score", 0)

    return render_template(
        "score_counter.html",
        team1_name=team1_name,
        team2_name=team2_name,
        team1_score=team1_score,
        team2_score=team2_score
    )


@app.route('/scores')
def scores():
    """Query to get all scores from the database"""
    try:
        db, cursor = get_db_cursor()
        if not db or not cursor:
            return "Database Error", 500

        cursor.execute("SELECT team1_name, team1_score, team2_name, team2_score, winner FROM scores ORDER BY id DESC")
        game_data = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return "Error fetching scores", 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    # Render the scores page and pass the game data to the template
    return render_template('scores.html', game_data=game_data)

@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.json
    team = data.get('team')
    new_score = data.get('score')
    winner = None

    cursor = None
    db = None

    try:
        # Update score for specified team
        if team == "team1":
            session["team1_score"] = new_score
        elif team == "team2":
            session["team2_score"] = new_score

        # Check for winner
        if session["team1_score"] >= 21:
            winner = f"{session['team1_name']} Wins!"
        elif session["team2_score"] >= 21:
            winner = f"{session['team2_name']} Wins!"

        # If there's a winner, insert final scores into database
        if winner:
            db, cursor = get_db_cursor()
            insert_game_data(session["team1_name"], session["team1_score"], session["team2_name"], session["team2_score"], winner)
            db.commit()
            # return jsonify({"winner": winner})
        
        # Always return something, even if there's no winner
        return jsonify({
            "team1_score": session["team1_score"],
            "team2_score": session["team2_score"],
            "winner": winner  # will be None if no one has won
        })


    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return "Internal Server Error", 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.route('/test-db')
def test_db():
    db, cursor = get_db_cursor()
    if not db or not cursor:
        return "Database connection failed!", 500

    try:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        cursor.close()
        db.close()
        return f"Connection successful! Tables: {tables}", 200
    except Exception as e:
        return f"Error querying the database: {e}", 500

@app.route("/debug")
def debug_session():
    # Show session content for debugging
    print("Current session data:", dict(session))
    return "Session data printed to console."



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

# Retrigger pipeline with user name and password updated 2 again
