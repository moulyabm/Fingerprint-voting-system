from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, init_db, Voter, Election, Candidate, Vote
from services import enroll_voter, authenticate_voter, issue_token, cast_vote, list_results
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fvoting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
init_db(app)

@app.route('/')
def home():
    now = datetime.utcnow()
    elections = Election.query.filter(Election.start_at <= now, Election.end_at >= now).all()
    return render_template('home.html', elections=elections)

@app.route('/enroll', methods=['GET','POST'])
def enroll():
    if request.method == 'POST':
        name = request.form['name']
        reg_no = request.form['reg_no']
        file = request.files['fingerprint']
        ok, msg = enroll_voter(name, reg_no, file)
        flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('enroll'))
    return render_template('enroll.html')

@app.route('/vote/<int:election_id>', methods=['GET','POST'])
def vote(election_id):
    election = Election.query.get_or_404(election_id)
    if request.method == 'POST':
        reg_no = request.form['reg_no']
        file = request.files['fingerprint']
        candidate_id = int(request.form['candidate_id'])
        ok, msg = authenticate_voter(reg_no, file)
        if ok:
            token = issue_token(reg_no, election_id)
            ok, msg = cast_vote(token, candidate_id)
        flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('home'))
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    return render_template('vote.html', election=election, candidates=candidates)

@app.route('/results/<int:election_id>')
def results(election_id):
    rows = list_results(election_id)
    return render_template('results.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
