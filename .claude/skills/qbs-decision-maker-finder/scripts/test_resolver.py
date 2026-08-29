"""Regression suite for the name matcher. Run before any batch write.

Every pair below is drawn from live CRM data. The same-person pairs must match
(or be flagged); the different-people pairs must NEVER match - a false match
writes a real, wrong human being into the decision-maker field.

    PAT=<token> python3 test_resolver.py     ->  exits non-zero on any error
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PAT", "unused-for-scoring")
from resolve_contact import score

SAME = [("Eric Porter","Erik","Porter"), ("Krista Gallio","Christa","Galleo"),
        ("Amy Greenlee","Amy","Greenlee Holland"), ("Grace Cusimano","Grace","Cucumano"),
        ("Joe Hayes","Joe","Hayes"), ("Dylan Rios","Dylan","Rios"),
        ("Jon Peterson","Jonathan","Peterson"), ("Steven Clark","Stephen","Clark"),
        ("Cathy Nguyen","Kathy","Nguyen"), ("Sabina Agarunova","Sabrina","Agarunova"),
        ("Christine Hall","Christina","Hall"), ("Britney Hurlbert","Brittany","Hurlburt")]

DIFFERENT = [("JP Bustamante","Michelle","Neto"), ("Mary Carmichael","Felipe","Perez"),
             ("Tammy Gallimore","Christa","Galleo"), ("Kim Colbert","Grace","Cucumano"),
             ("Sabina Agarunova","Adrian","Johnson"), ("John Smith","Jane","Smith"),
             ("Mark Jones","Mary","Jones"), ("Dan Brown","Don","Green"),
             ("Chris Taylor","Chris","Anderson"), ("Robert Levengood","Brian","Levinson"),
             ("Kim Colbert","Tim","Colbert"), ("Ron Davis","Rob","Davis"),
             ("Jan Miller","Dan","Miller"), ("Alan Wright","Alan","Bright"),
             ("Michael Smith","Michelle","Smith"), ("Jeff Cole","Jessica","Cole"),
             ("Paul Hart","Paula","Hunt"), ("Tom Baker","Tim","Barker")]

errors = auto = flagged = 0
for w, f, l in SAME:
    s = score(w, f, l)
    if s >= 2: auto += 1
    elif s == 1: flagged += 1; print("  flagged for a human: %-18s ~ %s %s" % (w, f, l))
    else: errors += 1; print("  MISSED  %-18s ~ %s %s  -> manufactures a false gap" % (w, f, l))
for w, f, l in DIFFERENT:
    if score(w, f, l) >= 2:
        errors += 1; print("  FALSE MATCH  %-18s ~ %s %s  -> would write the wrong person" % (w, f, l))

print("\nsame person   : %d auto-matched, %d flagged, %d missed  (of %d)" % (auto, flagged, errors and 0 or 0, len(SAME)))
print("different people: %d pairs, 0 may match" % len(DIFFERENT))
print("errors: %d" % errors)
sys.exit(1 if errors else 0)
