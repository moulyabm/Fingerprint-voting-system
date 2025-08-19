import cv2
import numpy as np
from models import db, Voter, Vote, Candidate
from datetime import datetime
import os, secrets

def extract_features(file):
    img_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(img, None)
    return descriptors

def match_features(desc1, desc2):
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(desc1, desc2)
    return len(matches)

def enroll_voter(name, reg_no, file):
    desc = extract_features(file)
    if desc is None:
        return False, "Invalid fingerprint image"
    voter = Voter.query.filter_by(reg_no=reg_no).first()
    if voter:
        return False, "Voter already enrolled"
    voter = Voter(name=name, reg_no=reg_no, template=desc.dumps())
    db.session.add(voter)
    db.session.commit()
    return True, "Voter enrolled successfully"

def authenticate_voter(reg_no, file):
    desc_probe = extract_features(file)
    voter = Voter.query.filter_by(reg_no=reg_no).first()
    if not voter:
        return False, "Voter not found"
    desc_db = np.loads(voter.template)
    score = match_features(desc_db, desc_probe)
    return (score > 10, "Authenticated" if score > 10 else "Authentication failed")

def issue_token(reg_no, election_id):
    return secrets.token_hex(16)

def cast_vote(token, candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return False, "Candidate not found"
    vote = Vote(election_id=candidate.election_id, voter_id=1, candidate_id=candidate_id)
    db.session.add(vote)
    db.session.commit()
    return True, "Vote cast successfully"

def list_results(election_id):
    rows = db.session.query(Candidate.name, db.func.count(Vote.id)).join(Vote, Candidate.id==Vote.candidate_id, isouter=True).filter(Candidate.election_id==election_id).group_by(Candidate.name).all()
    return rows
