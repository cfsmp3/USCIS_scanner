#!/bin/env python3
import requests
import os
from os import path
from bs4 import BeautifulSoup
from collections import defaultdict, Counter
import json
import re
import sys
import argparse
from pathlib import Path

case_prefix = "LIN21111"  # Day of the beast in USCIS epoch

"""
Yes, I know this is retarded. I just started with a couple of exceptions and
just can't be bothered to refactor this shit. It does what I need to do and
by green card is going to arrive real soon now.
"""


def get_case_type_and_step_from_body(body):
    form_regexp = ".*Form ([-a-zA-Z0-9_, ]*?),.*"
    matches = re.search(form_regexp, body)
    form = "UnknownForm"
    step = None
    if matches:
        form = matches.group(1)
    elif "I-765" in body:
        form = "I-765"
    elif "I-131" in body:
        form = "I-131"
    elif "I-485" in body:
        form = "I-485"
    elif "I-485J" in body:
        form = "I-485J"
    elif "I-130" in body:
        form = "I-130"

    if "Post Office delivered your new card" in body:
        step = "CardDelivered"
    elif "the Post Office picked up mail containing your new card" in body:
        step = "CardPickedUp"
    elif "the Post Office reported that they are returning your new card for" in body:
        step = "CardReturnedByUSPS"
    elif "we received your correspondence for" in body:
        step = "CorrespondenceReceived"
    elif "the Post Office returned your new card for" in body:
        step = "CardReturnedByUSPS"
    elif "At this time USCIS cannot provide you with information for your case" in body:
        step = "NoInfoAvailable"
    elif "we mailed your document for Receipt Number" in body:
        step = "DocumentMailed"
    elif "Your appeal was dismissed. Your case remains denied." in body:
        step = "AppealDismissed"
    elif "we ordered your new card for" in body:
        step = "CardOrdered"
    elif "we received your card for Receipt Number" in body and "letter from you":
        step = "CardReceivedWithLetter"
    elif "we sent you a termination notice for" in body:
        step = "TerminationNotice"
    elif "to the Department of State for visa processing." in body:
        step = "SentToDepartmentOfState"
    elif (
        "The appellate authority approved your appeal and mailed you a decision."
        in body
    ):
        step = "AppealApproved"
    elif "we mailed you a notice acknowledging withdrawal of your appeal" in body:
        step = "AppealWithdrawalAck"
    elif "we destroyed your card" in body:
        step = "CardDestroyed"
    elif (
        "we mailed you a notice explaining our intent to rescind the decision on your case"
        in body
    ):
        step = "DecisionRescinded"
    elif "we revoked the approval of your case" in body:
        step = "ApprovalRevoked"
    elif "we denied your request for expedited processing of your" in body:
        step = "ExpeditedRequestDenied"
    elif (
        "fingerprints relating to your" in body
        and "have been applied to your case" in body
    ):
        step = "Fingerprints_applied"
    elif "we mailed your new card for your" in body:
        step = "Card_mailed"
    elif "we received your Form" in body:
        step = "InitialFormReceived"
    elif "we denied your Form" in body:
        step = "FormDenied"
    elif "we received your response to our Request for Evidence for your Form" in body:
        step = "RFE_response_received"
    elif "we updated your date of birth for your" in body:
        step = "date_of_birth_updated"
    elif "we sent a request for additional evidence for your Form" in body:
        step = "RFE_sent"
    elif "the Post Office returned a notice we sent you for your Form" in body:
        step = "Post_office_returned_USCIS_notice"
    elif "we approved your Form" in body:
        step = "FormApproved"
    elif "we updated your name for your Form" in body:
        step = "NameUpdated"
    elif "we closed your Form" in body:
        step = "FormClosed"
    elif "we rejected your Form I-130, Petition for Alien Relative" in body:
        step = "FormRejected"
    elif (
        "Your interview for your Form I-130, Petition for Alien Relative" in body
        and "was completed, and your case must be reviewed." in body
    ):
        step = "InterviewCompletedMustReviewCase"
    elif "we sent you a duplicate notice" in body:
        step = "DuplicateNoticeSent"
    elif ", we began reviewing your " in body:
        step = "ReviewStarted"
    elif "we sent a request for initial evidence for your" in body:
        step = "RFIF_sent"
    elif "we received your request to withdraw your" in body:
        step = "WithdrawalRequestReceived"
    elif "we rescheduled an interview for your" in body:
        step = "InterviewRescheduled"
    elif "we requested that certain people associated with your" in body and "come to an appointment." in body and "No one came to the appointment, and this will significantly affect your case." in body:
        step = "AppointmentMissed"
    elif "we reopened" in body and "If you do not receive your reopening notice" in body:
        step = "FormReopened"
    elif "We mailed your document for your" in body:
        step = "DocumentMailed"
    elif "we transferred your" in body and "to another USCIS office." in body:
        step = "FormTransferred"
    return form, step


def get_case_info(case):
    tries = 0
    while tries < 3:
        try:
            r = requests.post(
                "https://egov.uscis.gov/casestatus/mycasestatus.do",
                data={"appReceiptNum": case, "initCaseSearch": "CHECK+STATUS"},
            )

            soup = BeautifulSoup(r.text, "html.parser")

            h4 = soup.find_all("h4")
            if h4:
                if "Validation Error(s)" in h4[0].text:
                    print("Case does not exist")
                    return None

            mydivs = soup.find_all("div", {"class": "rows text-center"})

            header = mydivs[0].find_all("h1")[0].text
            body = mydivs[0].find_all("p")[0].text
            print(body)
            print()
            type_and_step = get_case_type_and_step_from_body(body)
            return {"type": type_and_step[0], "step": type_and_step[1], "body": body}
        except:
            tries += 1

    print("Warning: Returned None due to exceptions")
    return None


def find_cases():
    cases = []
    case_types = defaultdict(list)
    unknown_forms = []
    unknown_steps = []
    for rs in range(0, 10):
        num_errors = 0
        for i in range(rs * 10000, (rs + 1) * 10000):
            next_case = case_prefix + "{:05d}".format(i)
            print(next_case)
            case_info = get_case_info(next_case)
            if not case_info:
                num_errors += 1
                if num_errors > 50:
                    print("50 fails, giving up")
                    break
                continue
            case_type = case_info["type"]
            case_step = case_info["step"]
            cases.append(next_case)
            case_types[case_type].append(next_case)
            if case_type == "UnknownForm":
                unknown_forms.append(case_info["body"])
            if not case_step:
                unknown_steps.append(case_info["body"])
            num_errors = 0
    return {
        "cases": cases,
        "case_types": case_types,
        "unknown_forms": unknown_forms,
        "unknown_steps": unknown_steps,
    }


parser = argparse.ArgumentParser(description="USCIS case scanner.")
parser.add_argument(
    "--case",
    type=str,
    help="Reference case number, used to extract date to process.",
    default="LIN21111XXXXX",
)
parser.add_argument(
    "--form",
    type=str,
    help="Form type we care about when updating current state",
    default="I-485",
)
parser.add_argument(
    "-u",
    "--unknown",
    help="Go over the list of Unknown events and try to process them again (useful only if there's been changes in code",
    action="store_true",
)

args = parser.parse_args()

if len(args.case) != 13:
    print("Invalid case number, it must be 13 characters")
    sys.exit(1)

case_prefix = args.case[0:8]

print(args)
form = args.form

state_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "case_states", case_prefix
)
print(state_dir)

valid_cases = path.join(state_dir, "cases.json")
form_counter_file = path.join(state_dir, f"{form}_counter.json")
form_counter_file_previous = path.join(state_dir, f"{form}_counter_previous.json")
form_diff_file_previous = path.join(state_dir, f"{form}_diff.json")
known_states = {}

Path(state_dir).mkdir(parents=True, exist_ok=True)

if not path.exists(valid_cases):
    print("Scanning for cases...")
    cases = find_cases()
    with open(valid_cases, "w") as f:
        f.write(json.dumps(cases))
else:
    with open(valid_cases, "r") as f:
        cases = json.load(f)

for case_type in cases["case_types"].keys():
    print(f'{case_type}: {len(cases["case_types"][case_type])}')

if args.unknown:
    print("Processing unknown events, will exit on first failure...")
    for ev in cases["unknown_events"]:
        if get_case_type_and_step_from_body(ev)[0] == "UnknownForm":
            print(ev)
            sys.exit(0)

previous_form_stats = None
if path.exists(form_counter_file):
    with open(form_counter_file, "r") as f:
        previous_form_stats = Counter(json.load(f))
    print("Loaded previous stats")
    print(previous_form_stats)
    os.rename(form_counter_file, form_counter_file_previous)


form_cases = cases["case_types"][form]
form_stats = Counter()
unparsed_bodies = []
for idx, case in enumerate(form_cases):
    print(f"[{idx+1} / {len(form_cases)}]: {case}")
    status = get_case_info(case)
    if not status:
        print("Couldn't get status, skipping this case")
        continue
    step = status["step"]
    if not step:
        body = status["body"]
        print(f"Unknown: {body}")
        form_stats["UknownStep"] += 1
        unparsed_bodies.append(body)
    else:
        form_stats[step] += 1
    print(status["step"])

print(form_stats)
with open(form_counter_file, "w") as f:
    f.write(json.dumps(form_stats))

if previous_form_stats:
    print("Comparison of previous run with this one:")
    form_stats.subtract(previous_form_stats)
    print(form_stats)
    with open(form_diff_file_previous, "w") as f:
        f.write(json.dumps(form_stats))

if len(unparsed_bodies):
    print(unparsed_bodies)
