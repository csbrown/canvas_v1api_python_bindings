import requests
import datetime
import joblib
import os
import collections
import functools
import pathlib
import re

CANVAS_DASH_EXTENSION_RE = re.compile("-\d(.[a-zA-Z0-9]+)$")

with open(os.path.join(pathlib.Path(__file__).parent, "canvas"),"r") as token_file:
    TOKEN = token_file.read().strip()
    if not TOKEN:
        raise Exception("You have to get an OAuth Token from Canvas, and put it into the 'canvas' file")

'2020-09-24T17:16:13Z'
def parsetime(t):
    utc_dt = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

class CanvasAPI():
    
    CANVAS_URL = "https://utah.instructure.com/api/v1"

    def __init__(self, token):
        self.token = token
        self.auth_header = {"Authorization": "Bearer " + token}

    def get(self, *args, **kwargs):
        if "headers" in kwargs:
            kwargs["headers"].update(self.auth_header)
        else:
            kwargs["headers"] = self.auth_header
        return requests.get(*args, **kwargs)

    def get_paginated(self, page_getter, n_jobs = 1):
        page_n = 1
        pages = joblib.Parallel(n_jobs = n_jobs)(
            joblib.delayed(page_getter)(i) for i in range(page_n, page_n + n_jobs)
        )
        all_pages = sum(pages, []) 
        while pages[-1]:
            page_n += n_jobs
            pages = joblib.Parallel(n_jobs = n_jobs)(
                joblib.delayed(page_getter)(i) for i in range(page_n, page_n + n_jobs)
            )
            all_pages += sum(pages, [])
        return all_pages


class ConversationsAPI(CanvasAPI):
    
    CONVERSATIONS_URL = CanvasAPI.CANVAS_URL + "/conversations"
    UNREAD_COUNT_URL = CONVERSATIONS_URL + "/unread_count"

    def get_unread_count(self):
        response = self.get(
            self.UNREAD_COUNT_URL
        )
        return int(response.json()["unread_count"])
        

class CourseAPI(CanvasAPI):

    COURSE_URL_FORMAT = CanvasAPI.CANVAS_URL + "/courses/{course_id}"

    def __init__(self, course_id, *args):
        super().__init__(*args)
        self.superargs = args
        self.course_id = course_id
        self.course_url = CourseAPI.COURSE_URL_FORMAT.format(course_id = course_id)


class QuizAPI(CourseAPI):
    
    QUIZ_LIST_URL_FORMAT = "{course_url}/quizzes"
    QUIZ_QUESTIONS_URL_FORMAT = QUIZ_LIST_URL_FORMAT + "/{quiz_id}/questions"
    
    def __init__(self, *args):
        super().__init__(*args)
        self.superargs = args
        self.quiz_url = QuizAPI.QUIZ_LIST_URL_FORMAT.format(course_url = self.course_url)
        self.quiz_questions_url = QuizAPI.QUIZ_QUESTIONS_URL_FORMAT.format(course_url = self.course_url)
    
    def get_quizzes(self, search=None):
        payload = []
        if search:
            payload.append(("search_term", search))
        response = self.get(
            self.quiz_url,
            params = payload
        )
        return response.json()

    def get_quiz_questions(self, quiz_id):
        url = self.quiz_questions_url.format(quiz_id = quiz_id)
        response = self.get(
            self.quiz_questions_url
        )
        return response.json()
    

class AssignmentGroupsAPI(CourseAPI):

    ASSIGNMENT_GROUPLIST_URL_FORMAT = "{course_url}/assignment_groups"

    def __init__(self, *args):
        super().__init__(*args)
        self.superargs = args
        self.assignment_group_url = AssignmentGroupsAPI.ASSIGNMENT_GROUPLIST_URL_FORMAT.format(course_url = self.course_url)

    def get_assignment_group_page(self, page):
        payload = [
            ("per_page", 50), 
            ("page", page), 
            ("include[]", "assignments"), 
            ("include[]", "assignment_visibility")
        ]
        response = self.get(
            self.assignment_group_url,
            params=payload
        )
        return response.json()

    def get_assignment_groups(self):
        return self.get_paginated(self.get_assignment_group_page)

    def investigate_assignment_groups(self):
        groups = self.get_assignment_groups()
        for group in groups:
            print(group["id"], group["name"], group["group_weight"])
        dive_id = int(input("which assignment group to dive? (id) "))
        for group in groups:
            if group["id"] == dive_id: break
        self.investigate_assignments(group["assignments"])
        
    def investigate_assignments(self, assignments):
        for assignment in assignments:
            if assignment["published"] and assignment["points_possible"]:
                print(assignment["id"], assignment["name"], assignment["points_possible"])
        dive_id = int(input("which assignment to dive? (id) "))
        for assignment in assignments:
            if assignment["id"] == dive_id: break
        submissions_api = AssignmentSubmissionsAPI(assignment["id"], *self.superargs)
        submissions_api.investigate_assignment_submissions()

class AssignmentSubmissionsAPI(CourseAPI):

    ASSIGNMENT_SUBMISSIONS_URL_FORMAT = "{course_url}/assignments/{assignment_id}/submissions"

    def __init__(self, assignment_id, *args):
        super().__init__(*args)
        self.assignment_id = assignment_id
        self.assignment_submissions_url = AssignmentSubmissionsAPI.ASSIGNMENT_SUBMISSIONS_URL_FORMAT.format(
            course_url = self.course_url, assignment_id = assignment_id)

    def get_assignment_submissions_page(self, page):
        payload = {"per_page": 50, "page": page, "include[]": "user"}
        #print("getting page {}".format(payload["page"]))
        response = self.get(
            self.assignment_submissions_url,
            params=payload
        )
        return response.json()

    def get_assignment_submissions(self):
        return self.get_paginated(self.get_assignment_submissions_page)

    def download_assignment_submission_files(self, dl_dir='.'):
        submissions = self.get_assignment_submissions()
        for submission in submissions:
            if "attachments" in submission:
                for attachment in submission["attachments"]:
                    file_content = requests.get(attachment["url"], allow_redirects=True)
                    with open(os.path.abspath(os.path.join(dl_dir, str(submission["user"]["sis_user_id"]) + "_" + attachment["filename"])), 'wb') as f:
                        f.write(file_content.content)

    def download_assignment_submission_files_parallel(self, dl_dir='.', n_jobs=32, rm_canvas_dash_extensions=False):
        submissions = self.get_assignment_submissions()
        submission_attachment_urls = []
        import pprint
        with open("blah", "w") as f:
            f.write(pprint.pformat(submissions))
        for submission in submissions:
            user_dir = os.path.join(dl_dir, submission["user"]["sortable_name"] + "_" + str(submission["user"]["sis_user_id"]))
            if "attachments" in submission:
                for attachment in submission["attachments"]:
                    filename = attachment["filename"]
                    if rm_canvas_dash_extensions:
                        filename = CANVAS_DASH_EXTENSION_RE.sub(r'\g<1>', filename) 
                    submission_attachment_urls.append(
                        (user_dir, filename, attachment['url'])
                    )
        joblib.Parallel(n_jobs=n_jobs)(joblib.delayed(self.download_file_and_write_content)(fname, url, dl_dir=user_dir) 
            for user_dir, fname, url in submission_attachment_urls)

    def download_file_and_write_content(self, fname, url, dl_dir='.'):
        file_content = requests.get(url, allow_redirects=True)
        os.makedirs(dl_dir, exist_ok=True)
        with open(os.path.abspath(os.path.join(dl_dir, fname)), 'wb') as f:
            f.write(file_content.content)
        

    def get_best_submission_by_user(self, submissions):
        # group by user
        user_submissions = collections.defaultdict(list)
        for submission in submissions:
            user_submissions[submission["user"]["sis_user_id"]].append(submission)
        # get the best submission for each user
        scores = []
        user_best = {}
        for user in user_submissions:
            user_best[user] = max(user_submissions[user], key=lambda x: x["score"] or 0)
            scores.append(user_best[user]["score"] or 0)
        return user_best, scores

    def investigate_assignment_submissions(self):
        submissions = self.get_assignment_submissions()
        user_best, scores = get_best_submission_by_user(submissions)
        plt.hist(scores)
        plt.show()


def get_assignment_scores(course_id, aid, aname):
    assignment_submissions_API = AssignmentSubmissionsAPI(aid, course_id, TOKEN)
    print("getting assignment submissions for {}".format(aname))
    submissions = assignment_submissions_API.get_assignment_submissions()
    user_best, scores = assignment_submissions_API.get_best_submission_by_user(submissions)
    assignment_scores = {}
    for user in user_best:
        assignment_scores[user] = user_best[user]["score"]
        #print(user_best)
    return assignment_scores

def get_student_assignment_grades(course_id, n_jobs = 16):
    student_assignments = {}
    print("getting assignments")
    assignment_group_API = AssignmentGroupsAPI(course_id, TOKEN)
    assignment_groups = assignment_group_API.get_assignment_groups()
    user_scores = {}
    for group in assignment_groups:
        group_scores = user_scores[group["id"]] = {}
        
        published_assignments = [assignment for assignment in group["assignments"] if assignment["published"]]

        assignment_scores = joblib.Parallel(n_jobs = n_jobs)(
            joblib.delayed(get_assignment_scores)(
                course_id, assignment["id"], assignment["name"]
            ) for assignment in published_assignments
        )
        
        for i, assignment in enumerate(published_assignments):
            group_scores[assignment["id"]] = assignment_scores[i]

    return user_scores, assignment_groups
    
def get_gradebook(course_id):
    import pandas as pd
    student_assignment_grades, assignment_groups = get_student_assignment_grades(course_id)
    users = set.union(*(
        set(student_assignment_grades[gid][aid].keys())
            for gid in student_assignment_grades 
                for aid in student_assignment_grades[gid]
        ))
    assignments = set.union(*(
        set(student_assignment_grades[gid].keys())
            for gid in student_assignment_grades
        ))
    df = pd.DataFrame(index = users, columns = assignments)
    for gid in student_assignment_grades:
        for aid in student_assignment_grades[gid]:
            for user in student_assignment_grades[gid][aid]:
                df.loc[user, aid] = student_assignment_grades[gid][aid][user]
    return df, assignment_groups

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--course_id", type=str, default="636288")
    args = parser.parse_args()

    gradebook = get_gradebook(args.course_id)
    print(gradebook)
